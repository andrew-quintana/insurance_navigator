#!/bin/bash

# Virtual Environment Management Script
# This script helps manage virtual environments across different projects

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to show usage
show_usage() {
    echo "Virtual Environment Management Script"
    echo ""
    echo "Usage: $0 <command> [options]"
    echo ""
    echo "Commands:"
    echo "  create [project_path]     Create a new virtual environment"
    echo "  activate [project_path]   Activate virtual environment for project"
    echo "  deactivate               Deactivate current virtual environment"
    echo "  install [project_path]    Install requirements for project"
    echo "  update [project_path]     Update requirements for project"
    echo "  clean [project_path]      Remove virtual environment"
    echo "  list                     List all virtual environments"
    echo "  status                   Show current environment status"
    echo ""
    echo "Examples:"
    echo "  $0 create ~/my-project"
    echo "  $0 activate ~/my-project"
    echo "  $0 install ~/my-project"
    echo "  $0 status"
}

# Function to get project path
get_project_path() {
    if [ -n "$1" ]; then
        echo "$1"
    else
        echo "$(pwd)"
    fi
}

# Function to get venv path
get_venv_path() {
    local project_path="$1"
    echo "$project_path/.venv"
}

# Function to check if venv exists
venv_exists() {
    local venv_path="$1"
    [ -d "$venv_path" ] && [ -f "$venv_path/bin/activate" ]
}

# Function to create virtual environment
create_venv() {
    local project_path="$1"
    local venv_path=$(get_venv_path "$project_path")
    
    if venv_exists "$venv_path"; then
        print_warning "Virtual environment already exists at $venv_path"
        return 0
    fi
    
    print_status "Creating virtual environment at $venv_path"
    python3 -m venv "$venv_path"
    
    # Activate and upgrade pip
    source "$venv_path/bin/activate"
    pip install --upgrade pip
    
    print_success "Virtual environment created successfully"
    
    # Check for requirements files
    if [ -f "$project_path/requirements.txt" ]; then
        print_status "Found requirements.txt, installing dependencies..."
        pip install -r "$project_path/requirements.txt"
        print_success "Dependencies installed from requirements.txt"
    fi
    
    if [ -f "$project_path/requirements-dev.txt" ]; then
        print_status "Found requirements-dev.txt, installing dev dependencies..."
        pip install -r "$project_path/requirements-dev.txt"
        print_success "Dev dependencies installed from requirements-dev.txt"
    fi
}

# Function to activate virtual environment
activate_venv() {
    local project_path="$1"
    local venv_path=$(get_venv_path "$project_path")
    
    if ! venv_exists "$venv_path"; then
        print_error "Virtual environment not found at $venv_path"
        print_status "Run '$0 create $project_path' to create it first"
        return 1
    fi
    
    print_status "Activating virtual environment for $project_path"
    print_warning "To activate manually, run: source $venv_path/bin/activate"
    
    # Create activation script
    cat > "$project_path/activate_venv.sh" << EOF
#!/bin/bash
# Auto-generated activation script
source "$venv_path/bin/activate"
echo "Virtual environment activated for $(basename "$project_path")"
echo "Python: \$(which python)"
echo "Pip: \$(which pip)"
EOF
    chmod +x "$project_path/activate_venv.sh"
    
    print_success "Activation script created: $project_path/activate_venv.sh"
}

# Function to deactivate virtual environment
deactivate_venv() {
    if [ -z "$VIRTUAL_ENV" ]; then
        print_warning "No virtual environment is currently active"
        return 0
    fi
    
    print_status "Deactivating virtual environment"
    deactivate
    print_success "Virtual environment deactivated"
}

# Function to install requirements
install_requirements() {
    local project_path="$1"
    local venv_path=$(get_venv_path "$project_path")
    
    if ! venv_exists "$venv_path"; then
        print_error "Virtual environment not found at $venv_path"
        print_status "Run '$0 create $project_path' to create it first"
        return 1
    fi
    
    source "$venv_path/bin/activate"
    
    if [ -f "$project_path/requirements.txt" ]; then
        print_status "Installing requirements from requirements.txt"
        pip install -r "$project_path/requirements.txt"
        print_success "Requirements installed"
    else
        print_warning "No requirements.txt found in $project_path"
    fi
    
    if [ -f "$project_path/requirements-dev.txt" ]; then
        print_status "Installing dev requirements from requirements-dev.txt"
        pip install -r "$project_path/requirements-dev.txt"
        print_success "Dev requirements installed"
    fi
}

# Function to update requirements
update_requirements() {
    local project_path="$1"
    local venv_path=$(get_venv_path "$project_path")
    
    if ! venv_exists "$venv_path"; then
        print_error "Virtual environment not found at $venv_path"
        return 1
    fi
    
    source "$venv_path/bin/activate"
    
    print_status "Updating pip and requirements"
    pip install --upgrade pip
    
    if [ -f "$project_path/requirements.txt" ]; then
        pip install --upgrade -r "$project_path/requirements.txt"
        print_success "Requirements updated"
    fi
    
    if [ -f "$project_path/requirements-dev.txt" ]; then
        pip install --upgrade -r "$project_path/requirements-dev.txt"
        print_success "Dev requirements updated"
    fi
}

# Function to clean virtual environment
clean_venv() {
    local project_path="$1"
    local venv_path=$(get_venv_path "$project_path")
    
    if ! venv_exists "$venv_path"; then
        print_warning "Virtual environment not found at $venv_path"
        return 0
    fi
    
    print_warning "This will remove the virtual environment at $venv_path"
    read -p "Are you sure? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf "$venv_path"
        print_success "Virtual environment removed"
    else
        print_status "Operation cancelled"
    fi
}

# Function to list virtual environments
list_venvs() {
    print_status "Searching for virtual environments..."
    echo ""
    
    find "$HOME" -name ".venv" -type d 2>/dev/null | while read -r venv_path; do
        local project_path=$(dirname "$venv_path")
        local project_name=$(basename "$project_path")
        
        if [ -f "$venv_path/bin/activate" ]; then
            echo "📁 $project_name"
            echo "   Path: $project_path"
            echo "   Venv: $venv_path"
            echo ""
        fi
    done
}

# Function to show status
show_status() {
    echo "Virtual Environment Status"
    echo "========================="
    echo ""
    
    if [ -n "$VIRTUAL_ENV" ]; then
        print_success "Virtual environment is ACTIVE"
        echo "  Environment: $VIRTUAL_ENV"
        echo "  Python: $(which python)"
        echo "  Pip: $(which pip)"
        echo "  Python version: $(python --version)"
    else
        print_warning "No virtual environment is currently active"
    fi
    
    echo ""
    echo "Current directory: $(pwd)"
    
    local current_venv=$(get_venv_path "$(pwd)")
    if venv_exists "$current_venv"; then
        print_success "Virtual environment available for current project"
        echo "  Venv path: $current_venv"
    else
        print_warning "No virtual environment found for current project"
    fi
}

# Main script logic
case "${1:-}" in
    "create")
        project_path=$(get_project_path "$2")
        create_venv "$project_path"
        ;;
    "activate")
        project_path=$(get_project_path "$2")
        activate_venv "$project_path"
        ;;
    "deactivate")
        deactivate_venv
        ;;
    "install")
        project_path=$(get_project_path "$2")
        install_requirements "$project_path"
        ;;
    "update")
        project_path=$(get_project_path "$2")
        update_requirements "$project_path"
        ;;
    "clean")
        project_path=$(get_project_path "$2")
        clean_venv "$project_path"
        ;;
    "list")
        list_venvs
        ;;
    "status")
        show_status
        ;;
    *)
        show_usage
        exit 1
        ;;
esac
