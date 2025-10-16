from src.gui.app import App
import sys


def main():
    """
    simTIM Main Entry Point

    This is the main entry point for the simTIM application.
    It launches the GUI interface for the simulation.
    """
    try:
        app = App()
        app.mainloop()
    except ImportError as e:
        print(f"Error: Could not import GUI components: {e}")
        print("Make sure all required packages are installed (requirements.txt)")
        sys.exit(1)
    except Exception as e:
        print(f"Error launching GUI: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

#TODO: Remove unused imports
#Todo: Remove code artefacts from all files
#Files already edited:
#-attacker.py, defender.py
#TODO: Add new tests
#TODO: Add Dashboard with overview
#TODO: Fix economic impact display
#TODO: Action creator
#TODO: implement help window for every tab using only one help.py file