import os

# The root folder of your project
root_dir = "."

# File extensions you want to include
extensions = (".py", ".html", ".css", ".js")

# Output file
output_file = "shelfchef_codebase.txt"

with open(output_file, "w", encoding="utf-8") as out:
    for folder, _, files in os.walk(root_dir):
        for file in files:
            if file.endswith(extensions):
                path = os.path.join(folder, file)
                out.write(f"\n\n===== FILE: {path} =====\n\n")
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    out.write(f.read())

print(f"✅ All code merged into {output_file}")
