import os
import sys

os.chdir(os.path.dirname(os.path.abspath(__file__)))

print(f"[DEBUG] Рабочая директория: {os.getcwd()}")
print(f"[DEBUG] tracks есть? {os.path.exists('tracks')}")
print(f"[DEBUG] config.json есть? {os.path.exists('config.json')}")

from menu import Menu

if __name__ == "__main__":
    Menu()