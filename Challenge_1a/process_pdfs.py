import os
import json
from unstructured.partition.pdf import partition_pdf
[cite_start]from unstructured.documents.elements import Title, NarrativeText, ListItem, Header, Footer # [cite: 5]

def extract_outline(pdf_path):
    """
    Extracts the title and a hierarchical outline (H1, H2, H3)
    from a PDF using the unstructured library.
    """
    title = ""
    outline = []
    page_number_map = {} # To store page numbers for elements

    try:
        # 1. Partition the PDF to get a list of elements using unstructured.
        # The 'partition_pdf' function is provided by the unstructured library.
        elements = partition_pdf(
            filename=pdf_path,
            # You can explore additional parameters from unstructured's documentation
            # to potentially improve parsing, e.g., 'strategy="hi_res"' for better
            # layout analysis, or 'include_metadata=True' if not default.
        )

        # 2. First pass: Identify the document title and collect page numbers for elements.
        # unstructured aims to identify a 'Title' element directly.
        for el in elements:
            if isinstance(el, Title):
                title = el.text.strip()
            # Store the page number associated with each element's start.
            # Elements usually have a 'metadata' attribute with 'page_number'.
            if hasattr(el, 'metadata') and hasattr(el.metadata, 'page_number'):
                page_number_map[el.id] = el.metadata.page_number

        # 3. Second pass: Iterate through elements to identify H1, H2, H3.
        # This is the most crucial part where you'll spend your time optimizing.
        # unstructured categorizes elements (e.g., Header, NarrativeText), and you
        # must infer the H1/H2/H3 hierarchy from these.
        # [cite_start]IMPORTANT: The hackathon guidelines state to NOT rely solely on font sizes. [cite: 94]

        # Variables to keep track of the most recently identified H1 and H2.
        # This helps in inferring the hierarchy of subsequent headings.
        current_h1_text = None
        current_h2_text = None

        for el in elements:
            text = el.text.strip()
            # Get the page number for the current element from our map.
            [cite_start]page = page_number_map.get(el.id, 0) # [cite: 42]

            # --- YOUR INTELLIGENT HEADING IDENTIFICATION LOGIC GOES HERE ---
            # [cite_start]This is the most crucial part of your solution for Round 1A and where you'll differentiate your solution. [cite: 29, 30]
            # You need to develop robust heuristics to determine if an
            # 'element' is an H1, H2, or H3. Consider:
            # 1.  **Element Type:** `Header` elements are primary candidates. Sometimes, `NarrativeText` might act as a heading if it's very distinct (e.g., all caps, short, followed by indented text).
            # 2.  **Text Content Patterns:** Look for common heading patterns:
            #     * **Capitalization:** All caps for major sections.
            #     * **Length:** Headings are usually short.
            #     * **Numbering/Prefixes:** "1. Introduction", "1.1 Subsection", "1.1.1 Detail". Regular expressions can be very useful here.
            #     * **Keywords:** Specific words that often start sections.
            # 3.  **Positional Information/Hierarchy:** While not relying on font size, you might infer hierarchy based on:
            #     * **Indentation:** Is the text visually indented?
            #     * **Flow:** Does it directly follow a major heading, indicating it's a sub-heading?
            #     * **Relationship to parent elements:** If `unstructured` provides parent-child relationships, use them.
            # [cite_start]4.  **`output_schema.json`:** Your final output for each outline item MUST have "level", "text", and "page" keys, conforming to the schema. [cite: 43]

            # Example Heuristics (YOU MUST REPLACE AND EXPAND THIS FOR ACCURACY):
            # This is a very basic, non-robust example. Your solution needs to be much more robust
            # to accurately distinguish H1, H2, H3 for diverse PDFs.
            if isinstance(el, Header): # 'Header' elements are generally the best starting point for headings
                # You need a more complex and reliable way to differentiate H1, H2, H3 here.
                # This could involve:
                # [cite_start]- Using a simple machine learning model (if within the <= 200MB model size limit). [cite: 59, 79]
                # - Developing a scoring system based on multiple features (length, caps, numerical patterns).
                # - Analyzing the context of where the header appears in the document structure provided by unstructured.

                # Placeholder logic - Refine this heavily:
                if len(text) < 40 and text.isupper(): # Very rough guess for H1 based on length and all caps
                    level = "H1"
                    [cite_start]outline.append({"level": level, "text": text, "page": page}) # [cite: 46]
                    current_h1_text = text # Update the most recent H1 found
                    current_h2_text = None # Reset H2 when a new H1 starts a new major section
                elif len(text) < 70 and text.istitle() and current_h1_text is not None: # Rough guess for H2
                    # Ensure an H1 was found previously to make it a sub-heading
                    level = "H2"
                    [cite_start]outline.append({"level": level, "text": text, "page": page}) # [cite: 47]
                    current_h2_text = text # Update the most recent H2 found
                elif len(text) < 100 and current_h2_text is not None: # Rough guess for H3
                    # Ensure an H2 was found previously to make it a sub-sub-heading
                    level = "H3"
                    [cite_start]outline.append({"level": level, "text": text, "page": page}) # [cite: 48]
            # Your logic might also need to explicitly check 'NarrativeText' elements if they commonly serve as headings in your test set.

    except Exception as e:
        # Print an error message if processing fails for a PDF.
        print(f"Error processing {pdf_path}: {e}")
        # Consider returning a specific error structure or logging more details if needed for debugging.
        return None, [] # Return empty title and outline on error

    # [cite_start]Ensure the final output structure (keys: "level", "text", "page") matches the 'output_schema.json'. [cite: 43]
    return title, outline

def process_pdfs_in_directory(input_dir, output_dir):
    """
    Processes all PDF files in the input_dir and saves their outlines as JSON in output_dir.
    """
    os.makedirs(output_dir, exist_ok=True) # Ensure output directory exists

    for filename in os.listdir(input_dir):
        if filename.lower().endswith(".pdf"):
            pdf_path = os.path.join(input_dir, filename)
            output_filename = os.path.splitext(filename)[0] + ".json"
            output_path = os.path.join(output_dir, output_filename)

            print(f"Processing {filename}...")
            doc_title, doc_outline = extract_outline(pdf_path)

            if doc_title is not None:
                result = {
                    [cite_start]"title": doc_title, # [cite: 44]
                    [cite_start]"outline": doc_outline # [cite: 45]
                }
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(result, f, indent=2)
                print(f"Successfully processed {filename} to {output_filename}")
            else:
                print(f"Failed to process {filename}. Skipping JSON output.")

if __name__ == "__main__":
    # The hackathon expects input from /app/input and output to /app/output
    # [cite_start]when run inside the Docker container. [cite: 69, 70, 71]
    INPUT_DIR = "/app/input"
    OUTPUT_DIR = "/app/output"

    process_pdfs_in_directory(INPUT_DIR, OUTPUT_DIR)