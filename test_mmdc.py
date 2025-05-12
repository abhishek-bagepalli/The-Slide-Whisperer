import subprocess

def test_mmdc_installation():
    try:
        result = subprocess.run(["powershell","mmdc", "--version"], capture_output=True, text=True, check=True)
        print(f"✅ Mermaid CLI is working! Version: {result.stdout.strip()}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error while trying to run mmdc: {e}")
    except FileNotFoundError:
        print("❌ 'mmdc' command not found. Make sure it's installed and in PATH.")

if __name__ == "__main__":
    test_mmdc_installation()
