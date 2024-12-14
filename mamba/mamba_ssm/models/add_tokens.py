import os

def process_paragraphs(input_dir, output_dir):
    # Walk through each subdirectory and file in the input directory
    for root, _, files in os.walk(input_dir):
        for file in files:
            if file.endswith('.txt'):
                input_file_path = os.path.join(root, file)
                
                # Create corresponding output directory structure
                relative_path = os.path.relpath(root, input_dir)
                output_file_dir = os.path.join(output_dir, relative_path)
                os.makedirs(output_file_dir, exist_ok=True)
                
                output_file_path = os.path.join(output_file_dir, file)
                
                # Read, process, and write the file
                with open(input_file_path, 'r', encoding='utf-8') as f:
                    paragraphs = f.read().split('\n')  # Split text by new lines for paragraphs
                
                # Add <im_start> and <im_end> tags to each paragraph
                processed_paragraphs = [
                    f"<|im_start|>{paragraph}<|im_end|>" if paragraph.strip() else "" 
                    for paragraph in paragraphs
                ]
                
                # Join paragraphs with new lines and write to the output file
                with open(output_file_path, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(processed_paragraphs))
