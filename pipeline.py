import sys
import os
import time
import subprocess
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"\n{'='*60}")
    print(f"🚀 {description}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error in {description}:")
        print(f"Command: {command}")
        print(f"Return code: {e.returncode}")
        if e.stdout:
            print(f"STDOUT:\n{e.stdout}")
        if e.stderr:
            print(f"STDERR:\n{e.stderr}")
        return False



def validate_file(file_path):
    """Validate input file exists and is supported format"""
    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' does not exist.")
        return False
    
    file_ext = Path(file_path).suffix.lower()
    supported_formats = ['.pdf', '.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.gif']
    
    if file_ext not in supported_formats:
        print(f"Error: Unsupported file format '{file_ext}'.")
        print(f"Supported formats: {', '.join(supported_formats)}")
        return False
    
    return True

def get_script_directory():
    """Get the directory where pipeline.py is located"""
    return os.path.dirname(os.path.abspath(__file__))

def main():
    print("🔄 Document Translation Pipeline")
    print("=" * 60)
    
    # Validate command line arguments
    if len(sys.argv) != 2:
        print("Usage: python pipeline.py <path_to_file>")
        print("\nExample:")
        print("  python pipeline.py /path/to/document.pdf")
        print("  python pipeline.py /path/to/image.jpg")
        sys.exit(1)
    
    input_file = sys.argv[1]
    script_dir = get_script_directory()
    
    # Validate input file
    if not validate_file(input_file):
        sys.exit(1)
    
    print(f"📄 Input file: {input_file}")
    print(f"📁 Script directory: {script_dir}")
    
    # Step 1: OCR Processing
    ocr_script = os.path.join(script_dir, "azure_ocr.py")
    ocr_command = f'python "{ocr_script}" "{input_file}"'
    
    if not run_command(ocr_command, "STEP 1: OCR Processing"):
        print("Pipeline failed at OCR step.")
        sys.exit(1)
    
    
    
    # Step 2: Translation
    translation_script = os.path.join(script_dir, "translation.py")
    translation_command = f'python "{translation_script}"'
    
    if not run_command(translation_command, "STEP 2: Text Translation"):
        print("Pipeline failed at translation step.")
        sys.exit(1)
    
    
    # Step 3: Visual Overlay Creation
    overlay_script = os.path.join(script_dir, "translated_content_over_canvas.py")
    overlay_command = f'python "{overlay_script}"'
    
    if not run_command(overlay_command, "STEP 3: Creating Visual Overlays"):
        print("Pipeline failed at visual overlay step.")
        sys.exit(1)
    
    # Pipeline completed successfully
    print("\n" + "=" * 60)
    print("COMPLETED SUCCESSFULLY!")
    print("\n" + "=" * 60)

    

if __name__ == "__main__":
    main()