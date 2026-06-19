# Sublime Text Setup for Virtual Environment

## Method 1: Using Project-Specific Build System

1. **Copy the build file to Sublime Text:**
   - Copy `Python_VirtualEnv.sublime-build` to your Sublime Text packages folder:
   - Location: `%APPDATA%\Sublime Text\Packages\User\`
   - Or go to: Sublime Text → Preferences → Browse Packages → User folder

2. **Select the build system:**
   - In Sublime Text, go to Tools → Build System
   - Select "Python_VirtualEnv" 

3. **Press F5 to run:**
   - Open any Python file in your project
   - Press `Ctrl+B` or `F5` to run with the virtual environment

## Method 2: Using Auto-Detecting Build System

1. **Copy the auto-detecting build file:**
   - Copy `Python_Auto_VEnv.sublime-build` to `%APPDATA%\Sublime Text\Packages\User\`

2. **This build system will automatically:**
   - Look for `.venv` folder in your project directory
   - Use the virtual environment Python if found
   - Fall back to system Python if no virtual environment exists

## Method 3: Project-Specific Settings

Create a `.sublime-project` file in your project root:

```json
{
    "folders": [
        {
            "path": "."
        }
    ],
    "settings": {
        "python_interpreter": "C:/Users/PC/myCoding/Realtime-Title-Translator/.venv/Scripts/python.exe"
    },
    "build_systems": [
        {
            "name": "Python (Virtual Env)",
            "cmd": ["C:/Users/PC/myCoding/Realtime-Title-Translator/.venv/Scripts/python.exe", "-u", "$file"],
            "file_regex": "^[ ]*File \"(...*?)\", line ([0-9]*)",
            "selector": "source.python"
        }
    ]
}
```

## Quick Setup Steps:

1. Copy one of the `.sublime-build` files to `%APPDATA%\Sublime Text\Packages\User\`
2. Restart Sublime Text
3. Open your Python file
4. Go to Tools → Build System → Select the new build system
5. Press `Ctrl+B` or `F5` to run

## Troubleshooting:

- If F5 doesn't work, use `Ctrl+B`
- Make sure the path to your virtual environment Python is correct
- Check that your virtual environment is activated and has the required packages installed
