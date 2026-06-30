#---------------------------------------------------------------------------------
#                                  Import Statements
#---------------------------------------------------------------------------------


import base64
import google.generativeai as genai
from dotenv import load_dotenv
import os 
from unstructured.partition.pdf import partition_pdf
from unstructured.documents.elements import Element, Text, Image, FigureCaption, Table, CompositeElement
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
import json
from unstructured.partition.pdf import partition_pdf

load_dotenv()
gemini_api = os.getenv("GEMINI_API_KEY")


#---------------------------------------------------------------------------------
#                                  Function Logic
#---------------------------------------------------------------------------------

def process_images_with_caption(raw_chunks, use_gemini = True):
    """
        Converting the Raw chunks for image from the unstructured library
        to new dict inorder to generate text from it for save in the db.
        Args:
            raw_chunks : Raw chunks from the unstructured library output of pdf 
            use_gemini : if its true means we will use Gemini 
        Returns:
            list[dict] : list of dict which have data of image
    """
    print("Inside_process_images")
    # Check the gemini api key is available or not
    if not gemini_api:
        raise ValueError("Cant find Gemini API")
    genai.configure(api_key=gemini_api)

    # Making a list for images data
    process_images = []

    # Iterate over the raw_chunks for getting only image data
    for idx,chunk in enumerate(raw_chunks):
        # Checking wheather the data is image or not 
        if isinstance(chunk,Image):
            print("We found an image.....")
            # Check idx + 1 is figure caption and if we found that it means time to get text from it
            if idx + 1 < len(raw_chunks) and isinstance(raw_chunks[idx+1] , FigureCaption):
                caption = raw_chunks[idx + 1].text 
            else:
                caption = None 

            # Okay we found the data now its time to create a dict from it  
            image_data = {
                "caption" : caption if caption else "No Caption",
                "image_text" : chunk.text,
                "base64_image" : chunk.metadata.image_base64,
                "content" : chunk.text,                             # Fall back if gemini api is not working save this...
                "content_type" : "image",
                "filename" : chunk.metadata.filename 
            }
            print("Converting to dict complete ... ")

            # Check if the we can use gemini or not 
            if use_gemini:
                # Model init
                print("Now Generative AI Part")
                model = genai.GenerativeModel("gemini-2.5-flash")
                # Getting image binary format 
                image_binary = base64.b64decode(image_data['base64_image'])
                # Generating prompt
                prompt = f"Describe the image in detail. The caption is : {image_data['caption']}. The image text is : {image_data['image_text']}. Please directly return the description without any additional text."
                # Invoking the model
                response = model.generate_content([
                    prompt,
                    {"mime_type" : "image/png" , "data" : image_binary}
                ])
                image_data['content'] = response.text 
                process_images.append(image_data)

    return process_images



def process_tables_with_description(raw_chunks , use_gemini = True):
    """
        Converting the Raw chunks for table from the unstructured library
        to new dict inorder to generate text from it for save in the db.
        Args:
            raw_chunks : Raw chunks from the unstructured library output of pdf 
            use_gemini : if its true means we will use Gemini 
        Returns:
            list[dict] : list of dict which have data of tables
    """

    # Check the gemini api key is available or not
    if not gemini_api:
        raise ValueError("Cant find Gemini API")
    genai.configure(api_key=gemini_api)

    # Making a list for table data
    process_tables = []

    # Iterate over the raw_chunks for getting only table data
    for idx , element in enumerate(raw_chunks):
        # Checking wheather the data is table or not
        if isinstance(element , Table):
            # Generating table_data dict
            table_data = {
                "table_as_html" : element.metadata.text_as_html,
                "table_text" : element.text,
                "content" : element.text,
                "content_type" : "table",
                "filename" : element.metadata.filename
            }
            print("Table Dict done.")

            # Check if we can use gemini or not 
            if use_gemini:
                # init the model
                model = genai.GenerativeModel("gemini-2.5-flash")
                # Prompt Creation
                prompt = (
                    "Analyse the following table and provide a detailed description of its contents,"
                    "including the structure,key data points and any notable trends or insights."
                    f"here is the table in HTML format : {table_data["table_as_html"]}"
                    "Directly analyze the table and provide a detailed description without any additional text."
                )
                # Getting response from the model
                response = model.generate_content([prompt])
                table_data["content"] = response.text
            
            else:
                # Using Ollama instead of Google API
                print("using ollama.....for table")
                # Init the model
                llm = ChatOllama(model="llama3.2:3b", temperature=0)
                # Prompt creation
                proper_prompt = ChatPromptTemplate.from_messages([
                    (
                        "system", 
                        "You are a precise data analysis assistant. Your sole task is to analyze "
                        "the provided HTML table and write a detailed text summary of its structure, "
                        "key data points, and insights. Do NOT copy, recreate, or output the table "
                        "or HTML code back to the user. Provide ONLY the final summary."
                    ),
                    (
                        "human", 
                        "Here is the table HTML format:\n\n{table_html}\n\nDirectly analyze the table "
                        "above and provide a detailed summary text."
                    )
                ])
                # Generating a Chain
                chain = proper_prompt | llm         # You can add StrOutputParser() if you want..
                # Invoking the chain
                result = chain.invoke({"table_html": table_data['table_as_html']})
                table_data["content"] = result.content
            # Append the data to the main list
            process_tables.append(table_data)
    return process_tables
    



def create_semantic_chunks(text_chunks):
    # Init the list for saving the text data
    processed_chunks = []
    # Iterate over the raw_chunks for getting only text data
    for idx,chunk in enumerate(text_chunks):
        # If its a text data 
        if isinstance(chunk , CompositeElement):
            # Generating chunk_data in dict
            chunk_data = {
                "content" : chunk.text,
                "content_type" : "text",
                "filename" : chunk.metadata.filename if chunk.metadata else None 
            }
            # Appending to main chunk list
            processed_chunks.append(chunk_data)
    return processed_chunks


#---------------------------------------------------------------------------------
#                                  Trial Runner for code
#---------------------------------------------------------------------------------


if __name__ == "__main__":

    # File location
    base_dir = "Files"
    pdf_file = "research_paper.pdf"
    pdf_file_path = f"{base_dir}/{pdf_file}"

    # raw_chunks = partition_pdf(
    #     filename=pdf_file_path,
    #     strategy="hi_res",
    #     infer_table_structure=True,
    #     extract_image_block_types=["Image" , "Figure" , "Table"],      # We want to extract image figure and table from pdf
    #     extract_image_block_to_payload=True,
    #     chunking_strategy=None
    # )

    # processed_images = process_images_with_caption(raw_chunks=raw_chunks,use_gemini=True)
    # with open("processed_images.json", "w") as f:
    #     json.dump(processed_images, f, indent=4)

    # processed_tables = process_tables_with_description(raw_chunks=raw_chunks,use_gemini=False)
    # with open("processed_tables.json" , "w") as f:
    #     json.dump(processed_tables , f , indent=4)


    text_chunks = partition_pdf(
        filename=pdf_file_path,
        strategy="hi_res",
        chunking_strategy="by_title",
        max_characters = 2000,
        combine_text_under_n_chars = 500,
        new_after_n_chars = 1500
    )

    semantic_chunks = create_semantic_chunks(text_chunks)
    for chunk in semantic_chunks:
        print(chunk)