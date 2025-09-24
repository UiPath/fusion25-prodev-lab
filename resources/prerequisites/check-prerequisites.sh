#!/usr/bin/env bash

# Prerequisites Checker for Company Agent with UiPath (macOS/Linux)
# This script checks if all required software is installed and properly configured
# Excludes UiPath-specific prerequisites

total_checks=0
passed_checks=0
warnings=()
errors=()

# Color output functions
print_color() {
    local message="$1"
    local type="$2"

    case "$type" in
        "Success") echo -e "\033[32m$message\033[0m" ;;
        "Error") echo -e "\033[31m$message\033[0m" ;;
        "Warning") echo -e "\033[33m$message\033[0m" ;;
        "Info") echo -e "\033[36m$message\033[0m" ;;
        "Header")
            echo ""
            echo -e "\033[34m============================================================\033[0m"
            echo -e "\033[34m$message\033[0m"
            echo -e "\033[34m============================================================\033[0m"
            ;;
        *) echo "$message" ;;
    esac
}

# Test if a command exists and optionally check version
test_command() {
    local command="$1"
    local display_name="$2"
    local min_version="$3"
    local version_command="$4"
    local optional="$5"

    ((total_checks++))
    printf "Checking %s... " "$display_name"

    if command -v "$command" >/dev/null 2>&1; then
        if [[ -n "$min_version" ]]; then
            local version_output
            version_output=$($command $version_command 2>&1)

            # Extract version number using regex
            if [[ $version_output =~ ([0-9]+\.?[0-9]*\.?[0-9]*) ]]; then
                local installed_version="${BASH_REMATCH[1]}"

                # Simple version comparison (assumes semantic versioning)
                if [[ "$(printf '%s\n' "$min_version" "$installed_version" | sort -V | head -n1)" == "$min_version" ]]; then
                    print_color "[OK] Found version $installed_version" "Success"
                    ((passed_checks++))
                else
                    local message="[X] Version $installed_version found, but $min_version or higher required"
                    if [[ "$optional" == "true" ]]; then
                        print_color "$message" "Warning"
                        warnings+=("$display_name: $message")
                    else
                        print_color "$message" "Error"
                        errors+=("$display_name: $message")
                    fi
                fi
            else
                print_color "[OK] Found (version unknown)" "Success"
                ((passed_checks++))
            fi
        else
            print_color "[OK] Found" "Success"
            ((passed_checks++))
        fi
    else
        local message="[X] Not found"
        if [[ "$optional" == "true" ]]; then
            print_color "$message (Optional)" "Warning"
            warnings+=("$display_name: Not installed (optional)")
        else
            print_color "$message" "Error"
            errors+=("$display_name: Not installed")
        fi
    fi
}

# Test OS version
test_os_version() {
    ((total_checks++))
    printf "Checking OS version... "

    if [[ "$OSTYPE" == "darwin"* ]]; then
        local os_version
        os_version=$(sw_vers -productVersion)
        local major_version
        major_version=$(echo "$os_version" | cut -d. -f1)

        if [[ "$major_version" -ge 11 ]]; then
            print_color "[OK] macOS $os_version" "Success"
            ((passed_checks++))
        else
            print_color "[X] macOS version too old ($os_version)" "Error"
            errors+=("macOS - Version too old. Requires macOS 11 (Big Sur) or later")
        fi
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        local os_info
        if [[ -f /etc/os-release ]]; then
            os_info=$(grep PRETTY_NAME /etc/os-release | cut -d'"' -f2)
            print_color "[OK] $os_info" "Success"
            ((passed_checks++))
        else
            print_color "[OK] Linux (unknown distribution)" "Success"
            ((passed_checks++))
        fi
    else
        print_color "[!] Unknown OS ($OSTYPE)" "Warning"
        warnings+=("OS: Unknown operating system")
        ((passed_checks++))
    fi
}

# Main execution
clear
print_color "Prerequisites Checker for Company Agent with UiPath" "Header"
print_color "Checking prerequisites..." "Info"
echo ""

print_color "CHECKING PREREQUISITES" "Info"
echo "----------------------------------------"

test_os_version
test_command "uv" "UV Package Manager" "" "--version"
test_command "git" "Git" "" "--version"
test_command "node" "Node.js" "14.0" "--version"
test_command "npm" "npm" "" "--version"
test_command "jupyter" "Jupyter" "" "--version"
test_command "cursor" "Cursor" "" "--version"

# Summary
echo ""
print_color "SUMMARY" "Header"
echo "Checks passed: $passed_checks / $total_checks"

if [[ ${#errors[@]} -gt 0 ]]; then
    echo ""
    print_color "ERRORS (Must be fixed):" "Error"
    for error in "${errors[@]}"; do
        echo "  • $error"
    done
fi

if [[ ${#warnings[@]} -gt 0 ]]; then
    echo ""
    print_color "WARNINGS (Recommended to fix):" "Warning"
    for warning in "${warnings[@]}"; do
        echo "  • $warning"
    done
fi

# Installation commands
if [[ ${#errors[@]} -gt 0 ]]; then
    echo ""
    print_color "INSTALLATION COMMANDS" "Info"
    echo "----------------------------------------"

    for error in "${errors[@]}"; do
        if [[ $error == *"UV Package Manager"* ]]; then
            echo "Install UV:"
            if [[ "$OSTYPE" == "darwin"* ]]; then
                echo "  • Using Homebrew: brew install uv"
            else
                echo "  • Using pip: pip install uv"
            fi
            echo "  • Or using pipx: pipx install uv"
            echo "  • Or download from: https://github.com/astral-sh/uv"
            echo ""
        fi


        if [[ $error == *"Git"* ]]; then
            echo "Install Git:"
            if [[ "$OSTYPE" == "darwin"* ]]; then
                echo "  • Using Homebrew: brew install git"
                echo "  • Or download from: https://git-scm.com/download/mac"
            else
                echo "  • Ubuntu/Debian: sudo apt-get install git"
                echo "  • CentOS/RHEL: sudo yum install git"
                echo "  • Or download from: https://git-scm.com/download/linux"
            fi
            echo ""
        fi

        if [[ $error == *"Node.js"* ]]; then
            echo "Install Node.js:"
            if [[ "$OSTYPE" == "darwin"* ]]; then
                echo "  • Using Homebrew: brew install node"
            else
                echo "  • Ubuntu/Debian: sudo apt-get install nodejs npm"
                echo "  • CentOS/RHEL: sudo yum install nodejs npm"
            fi
            echo "  • Or download from: https://nodejs.org/"
            echo ""
        fi

        if [[ $error == *"Jupyter"* ]]; then
            echo "Install Jupyter:"
            echo "  • Using uv: uv pip install jupyter"
            echo "  • Or using conda: conda install jupyter"
            echo "  • Full instructions: https://jupyter.org/install"
            echo ""
        fi

        if [[ $error == *"Cursor"* ]]; then
            echo "Install Cursor:"
            echo "  • Download from: https://cursor.sh/"
            echo "  • AI-powered code editor"
            echo ""
        fi
    done
fi

echo ""
if [[ ${#errors[@]} -eq 0 ]]; then
    print_color "[OK] All critical prerequisites are satisfied!" "Success"
    print_color "You can proceed with the setup." "Success"
else
    print_color "[X] Some critical prerequisites are missing." "Error"
    print_color "Please install the missing components before proceeding." "Error"
fi

echo ""