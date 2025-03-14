from src.processor import process_data

def main():
    """
    Main entry point of the application.
    """
    sample_data = "hello world"
    processed = process_data(sample_data)
    print(f"Processed Data: {processed}")

if __name__ == "__main__":
    main()
