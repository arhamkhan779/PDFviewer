from pathlib import Path
import yaml

def Load_Yaml(path:Path) -> any:
    """
    Reads a YAML file and returns its contents as a dictionary.
        
    :param file_path: Path to the YAML file.
    :return: Dictionary containing the YAML file data.
    """
    try:
        with open(path, "r") as file:
            data = yaml.safe_load(file)
        return data
    except FileNotFoundError:
        print(f"Error: The file '{path}' was not found.")
        return None
    except yaml.YAMLError as e:
        print(f"Error parsing YAML file: {e}")
        return None
    
def generate_sequential_id(existing_ids, prefix="ID_", length=3):
    """Generate the next unique sequential ID."""
    
    if not existing_ids:  # If no existing IDs, start from 001
        return f"{prefix}{'1'.zfill(length)}"
    
    # Extract numerical parts and find the highest number
    existing_numbers = [
        int(id.replace(prefix, "")) for id in existing_ids if id.startswith(prefix)
    ]
    
    next_number = max(existing_numbers) + 1  # Increment the highest number
    new_id = f"{prefix}{str(next_number).zfill(length)}"  # Format with leading zeros
    
    return new_id