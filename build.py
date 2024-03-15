import os
import time
import subprocess
import sqlite3
import hashlib


def create_database(conn):
    cursor = conn.cursor()
    cursor.execute(
        """CREATE TABLE IF NOT EXISTS files (path TEXT PRIMARY KEY, hash TEXT)"""
    )
    conn.commit()


def get_file_hash(file_path):
    with open(file_path, "rb") as f:
        file_hash = hashlib.blake2b(f.read()).hexdigest()
    return file_hash


def convert_with_pandoc(input_file, output_file, css_file, js_file, header):
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
                "-B", # "--include-before-body="
                header,

                
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
    header = "header.html"

    # Connect to the database
    conn = sqlite3.connect(database_file)
    create_database(conn)

    # Load state from the database
    cursor = conn.cursor()
    cursor.execute("SELECT path, hash FROM files")
    created_files = {row[0]: row[1] for row in cursor.fetchall()}

    for root, _, files in os.walk(directory_path):
        for file in files:
            if file.endswith(".md"):
                file_path = os.path.join(root, file)
                file_hash = get_file_hash(file_path)
                if (
                    file_path not in created_files
                    or created_files[file_path] != file_hash
                ):
                    output_file = os.path.join(
                        output_directory, file.replace(".md", ".html")
                    )
                    convert_with_pandoc(file_path, output_file, css_file, js_file, header)
                    # Update or insert the file in the database
                    cursor.execute(
                        "REPLACE INTO files (path, hash) VALUES (?, ?)",
                        (file_path, file_hash),
                    )
                    conn.commit()

    conn.close()


if __name__ == "__main__":
    main()
