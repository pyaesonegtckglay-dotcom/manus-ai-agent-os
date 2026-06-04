import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import TaskInput from '@/components/TaskInput';

describe('TaskInput', () => {
  it('renders task input form', () => {
    render(<TaskInput onSubmit={jest.fn()} />);
    
    expect(screen.getByText('What would you like me to do?')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Describe your task...')).toBeInTheDocument();
  });

  it('shows example suggestions', () => {
    render(<TaskInput onSubmit={jest.fn()} />);
    
    const examples = screen.getAllByText(/Search for/);
    expect(examples.length).toBeGreaterThan(0);
  });

  it('calls onSubmit with task description', async () => {
    const mockSubmit = jest.fn();
    render(<TaskInput onSubmit={mockSubmit} />);
    
    const input = screen.getByPlaceholderText('Describe your task...');
    const submitButton = screen.getByRole('button', { name: /Execute/i });
    
    fireEvent.change(input, { target: { value: 'Test task description' } });
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(mockSubmit).toHaveBeenCalledWith('Test task description');
    });
  });

  it('shows priority selector', () => {
    render(<TaskInput onSubmit={jest.fn()} />);
    
    expect(screen.getByText('Priority')).toBeInTheDocument();
  });

  it('disables submit when input is empty', () => {
    render(<TaskInput onSubmit={jest.fn()} />);
    
    const submitButton = screen.getByRole('button', { name: /Execute/i });
    expect(submitButton).toBeDisabled();
  });

  it('clears input after submission', async () => {
    const mockSubmit = jest.fn();
    render(<TaskInput onSubmit={mockSubmit} />);
    
    const input = screen.getByPlaceholderText('Describe your task...');
    
    fireEvent.change(input, { target: { value: 'Test task' } });
    fireEvent.click(screen.getByRole('button', { name: /Execute/i }));
    
    await waitFor(() => {
      expect(input).toHaveValue('');
    });
  });

  it('highlights example on click', () => {
    render(<TaskInput onSubmit={jest.fn()} />);
    
    const example = screen.getByText('Write and deploy a React component');
    fireEvent.click(example);
    
    const input = screen.getByPlaceholderText('Describe your task...');
    expect(input).toHaveValue('Write and deploy a React component to GitHub');
  });
});