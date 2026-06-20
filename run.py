import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))


from menu import Menu

if __name__ == "__main__":
    Menu()