import os
import time
import subprocess
import sqlite3

# from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class MyHandler(FileSystemEventHandler):
    def __init__(self, conn, output_directory):
        super().__init__()
        self.conn = conn
        self.created_files = set()
        self.output_directory = output_directory

    def on_created(self, event):
        if event.is_directory:
            return
        self.created_files.add(event.src_path)


def create_database(conn):
    cursor = conn.cursor()
    cursor.execute(
        """CREATE TABLE IF NOT EXISTS files
                    (path TEXT PRIMARY KEY)"""
    )
    conn.commit()


def convert_with_pandoc(input_file, output_file, css_file, js_file):
    try:
        subprocess.run(
            [
                "pandoc",
                input_file,
                "-o",
                output_file,
                "--css",
                css_file,
                "--include-in-header",
                js_file,
                "--katex",
            ],
            check=True,
        )
        print(f"Converted {input_file} to {output_file}")
    except subprocess.CalledProcessError as e:
        print("Error:", e)


def main():
    # Initialize directory and file paths
    directory_path = "/Users/orobus/Documents/dev/robuso.github.io/_writing_folder"
    output_directory = "/Users/orobus/Documents/dev/robuso.github.io/website/blog/posts"
    css_file = "/style.css"
    js_file = "/Users/orobus/Documents/dev/robuso.github.io/script.js"
    database_file = "/Users/orobus/Documents/dev/robuso.github.io/files.db"

    # Connect to the database
    conn = sqlite3.connect(database_file)
    create_database(conn)

    # Load state from the database
    cursor = conn.cursor()
    cursor.execute("SELECT path FROM files")
    created_files = {row[0] for row in cursor.fetchall()}

    # Initialize the event handler
    event_handler = MyHandler(conn, output_directory)

    # Check for newly created files and convert them
    for root, _, files in os.walk(directory_path):
        for file in files:
            if file.endswith(".md"):
                file_path = os.path.join(root, file)
                if file_path not in created_files:
                    output_file = os.path.join(
                        output_directory, file.replace(".md", ".html")
                    )
                    convert_with_pandoc(file_path, output_file, css_file, js_file)
                    # Add the file to the database
                    cursor.execute("INSERT INTO files (path) VALUES (?)", (file_path,))
                    conn.commit()

    conn.close()


if __name__ == "__main__":
    main()
