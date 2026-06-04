-- Manus AI Agent OS - Supabase Schema
-- Run this SQL in the Supabase SQL Editor to set up the database

-- Enable vector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- =============================================
-- USERS TABLE
-- =============================================
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    name TEXT,
    avatar_url TEXT,
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for email lookups
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- =============================================
-- SESSIONS TABLE
-- =============================================
CREATE TABLE IF NOT EXISTS sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name TEXT,
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'paused', 'completed', 'failed')),
    sandbox_id TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for user sessions
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions(status);

-- =============================================
-- TASK HISTORY TABLE
-- =============================================
CREATE TABLE IF NOT EXISTS task_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES sessions(id) ON DELETE SET NULL,
    description TEXT NOT NULL,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'queued', 'running', 'completed', 'failed', 'cancelled')),
    priority TEXT DEFAULT 'normal' CHECK (priority IN ('low', 'normal', 'high', 'urgent')),
    timeout INTEGER DEFAULT 3600,
    result JSONB,
    error TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ
);

-- Indexes for task queries
CREATE INDEX IF NOT EXISTS idx_tasks_session_id ON task_history(session_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON task_history(status);
CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON task_history(created_at DESC);

-- =============================================
-- MEMORY EMBEDDINGS TABLE
-- =============================================
CREATE TABLE IF NOT EXISTS memory_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    embedding VECTOR(1536),
    memory_type TEXT DEFAULT 'general' CHECK (memory_type IN ('general', 'conversation', 'knowledge', 'preference')),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for vector similarity search (IVF index for approximate search)
CREATE INDEX IF NOT EXISTS idx_memory_embeddings_session_id ON memory_embeddings(session_id);
CREATE INDEX IF NOT EXISTS idx_memory_embeddings ON memory_embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- =============================================
-- TOOL CONFIGS TABLE
-- =============================================
CREATE TABLE IF NOT EXISTS tool_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    tool_type TEXT NOT NULL CHECK (tool_type IN ('browser', 'terminal', 'file', 'api', 'custom')),
    config JSONB NOT NULL,
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for user tools
CREATE INDEX IF NOT EXISTS idx_tool_configs_user_id ON tool_configs(user_id);

-- =============================================
-- FUNCTION FOR MATCHING MEMORIES (Vector Search)
-- =============================================
CREATE OR REPLACE FUNCTION match_memories(
    query_embedding VECTOR(1536),
    match_threshold FLOAT DEFAULT 0.7,
    match_count INT DEFAULT 5,
    search_session_id UUID DEFAULT NULL
)
RETURNS TABLE (
    id UUID,
    session_id UUID,
    content TEXT,
    metadata JSONB,
    similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        me.id,
        me.session_id,
        me.content,
        me.metadata,
        1 - (me.embedding <=> query_embedding) AS similarity
    FROM memory_embeddings me
    WHERE
        (search_session_id IS NULL OR me.session_id = search_session_id)
        AND me.embedding IS NOT NULL
        AND 1 - (me.embedding <=> query_embedding) > match_threshold
    ORDER BY me.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- =============================================
-- FUNCTION FOR EMBEDDING TEXT (placeholder for external embedding service)
-- =============================================
CREATE OR REPLACE FUNCTION generate_embedding(text_input TEXT)
RETURNS VECTOR(1536)
LANGUAGE plpgsql
AS $$
DECLARE
    embedding_result VECTOR(1536);
BEGIN
    -- This is a placeholder. In production, you would call an external
    -- embedding service like OpenAI, HuggingFace, or a self-hosted model.
    -- For now, return a zero vector as a placeholder.
    SELECT array_to_vector(array_fill(0, ARRAY[1536])) INTO embedding_result;
    RETURN embedding_result;
END;
$$;

-- =============================================
-- TRIGGERS FOR UPDATED_AT
-- =============================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply to all tables with updated_at
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_sessions_updated_at
    BEFORE UPDATE ON sessions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tasks_updated_at
    BEFORE UPDATE ON task_history
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tool_configs_updated_at
    BEFORE UPDATE ON tool_configs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================
-- ROW LEVEL SECURITY (RLS)
-- =============================================
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE task_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE memory_embeddings ENABLE ROW LEVEL SECURITY;
ALTER TABLE tool_configs ENABLE ROW LEVEL SECURITY;

-- Users: Users can only see/edit their own data
CREATE POLICY "Users can view own data" ON users
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update own data" ON users
    FOR UPDATE USING (auth.uid() = id);

-- Sessions: Users can access their own sessions
CREATE POLICY "Users can view own sessions" ON sessions
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can create own sessions" ON sessions
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own sessions" ON sessions
    FOR UPDATE USING (auth.uid() = user_id);

-- Tasks: Users can access tasks in their sessions
CREATE POLICY "Users can view own tasks" ON task_history
    FOR SELECT USING (
        session_id IN (SELECT id FROM sessions WHERE user_id = auth.uid())
    );

CREATE POLICY "Users can create own tasks" ON task_history
    FOR INSERT WITH CHECK (
        session_id IN (SELECT id FROM sessions WHERE user_id = auth.uid())
    );

CREATE POLICY "Users can update own tasks" ON task_history
    FOR UPDATE USING (
        session_id IN (SELECT id FROM sessions WHERE user_id = auth.uid())
    );

-- Memory: Users can access memories in their sessions
CREATE POLICY "Users can view own memories" ON memory_embeddings
    FOR SELECT USING (
        session_id IN (SELECT id FROM sessions WHERE user_id = auth.uid())
    );

CREATE POLICY "Users can create own memories" ON memory_embeddings
    FOR INSERT WITH CHECK (
        session_id IN (SELECT id FROM sessions WHERE user_id = auth.uid())
    );

-- Tool configs: Users can manage their own tools
CREATE POLICY "Users can manage own tools" ON tool_configs
    FOR ALL USING (auth.uid() = user_id);

-- =============================================
-- SAMPLE DATA (for testing)
-- =============================================
-- Insert a test user (replace with your user ID after auth setup)
-- INSERT INTO users (id, email, name) VALUES 
--     ('00000000-0000-0000-0000-000000000001', 'test@example.com', 'Test User');

-- =============================================
-- COMMENTS
-- =============================================
COMMENT ON TABLE users IS 'User accounts and preferences';
COMMENT ON TABLE sessions IS 'Agent execution sessions';
COMMENT ON TABLE task_history IS 'Completed and pending tasks';
COMMENT ON TABLE memory_embeddings IS 'Vector embeddings for semantic memory';
COMMENT ON TABLE tool_configs IS 'Custom tool definitions per user';
COMMENT ON FUNCTION match_memories IS 'Find similar memories using vector similarity';
COMMENT ON FUNCTION generate_embedding IS 'Generate embeddings for text (requires external service)';

-- =============================================
-- VERIFY SETUP
-- =============================================
DO $$
BEGIN
    -- Verify vector extension is available
    IF EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector') THEN
        RAISE NOTICE '✓ Vector extension enabled';
    ELSE
        RAISE WARNING '⚠️ Vector extension not found. Run: CREATE EXTENSION vector;';
    END IF;
    
    -- Verify tables exist
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'users') THEN
        RAISE NOTICE '✓ Tables created successfully';
    END IF;
END $$;