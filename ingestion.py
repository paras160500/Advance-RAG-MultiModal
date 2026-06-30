#---------------------------------------------------------------------------------
#                                  Import Statements
#---------------------------------------------------------------------------------
from opensearchpy import OpenSearch,helpers
from helper import get_embedding,get_opensearch_client
from unstructured.partition.pdf import partition_pdf
from chunking import process_images_with_caption,process_tables_with_description,create_semantic_chunks
#---------------------------------------------------------------------------------
#                                   Logic Functions
#---------------------------------------------------------------------------------
def create_index_if_not_exists(client : OpenSearch , index_name : str):
    """
        Create an index if the index is not available on the client
        Args:
            client : OpenSearch client
            index_name : name of the index in string
    """
    if client.indices.exists(index=index_name):
        # If index exists then delete it...
        print(f"Index : {index_name} already exists.")
        client.indices.delete(index = index_name)

        # Creating mapping for index
        mappings = {
            "mappings" : {
                "properties" : {
                    "content" : {"type" : "text"},
                    "content_type" : {"type" : "keyword"},
                    "filename" : {"type" : "keyword"},
                    "embedding" : {"type" : "dense_vector" , "dims" : 768}
                }
            },
            "settings" : {
                "index" : {
                    "knn" : True,
                    "knn.space_type" : "cosinesimilarity"
                }
            }
        }

        try:
            client.indices.create(index = index_name , body = mappings)
            print(f"Index {index_name} created successfully.")
        except Exception as e:
            print("Error in creating index :- " , str(e))
            raise


def prepare_chunks_for_ingestion(chunks):
    """
        Preparing chunks for ingestion
        Args:
            chunks: The data which we want to ingest in db
        Returns:
            return list of dict having information about chunks
    """
    prepared_chunks = []

    # enumerate over the chunks for creating chunk data for each chunk with embedding
    for idx,chunk in enumerate(chunks):
        if not chunk.get("content"):
            print(f"Skipping chunk on index : {idx}")
            continue 

        # Generate embedding for chunk content 
        chunk['embedding'] = get_embedding(chunk['content'])

        # Prepare the chunk data
        chunk_data = {
            "content" : chunk.get("content" , ""),
            "content_type" : chunk.get("content_type" , "text"),
            "filename" : chunk.get("filename" , None),
            "embedding" : chunk.get("embedding" , None)
        }
        prepared_chunks.append(chunk_data)

    return prepared_chunks


def ingest_chunks_to_opensearch(client , index_name , chunks):
    """
        Ingest the prepared chunks to the specified Opensearch index
        Args:
            client : Client of opensearch
            index_name : name of index where to push the chunks
            chunks : Actual data to be push in the db
    """
    actions = []
    for chunk in chunks:
        action = {
            "_index" : index_name,
            "_source" : chunk 
        }
        actions.append(action)

    try:
        helpers.bulk(client , actions)
        print(f"Ingested {len(actions)} chunks into index {index_name}")
    except Exception as e:
        print(f"Error ingesting chunks into index {index_name} : {str(e)}")


def ingest_all_content_into_opensearch(process_images , processed_tables , semantic_chunks , index_name):
    """
        Main function to ingest all the content into opensearch
        Args:
            process_images : list of dict having image data
            processed_tables : list of dict having table data
            semantic_chunks : list of dict having text data
            index_name : which index we want to push the data
    """

    # Generating Client
    client = get_opensearch_client("localhost" , 9200)

    # Create index if it does not exists
    create_index_if_not_exists(client , index_name)

    # Prepare and ingest images
    image_chunks = prepare_chunks_for_ingestion(process_images)
    ingest_chunks_to_opensearch(client , index_name , image_chunks)

    # Prepare and ingest tables
    table_chunks = prepare_chunks_for_ingestion(processed_tables)
    ingest_chunks_to_opensearch(client , index_name , table_chunks)

    # Prepare and ingest semantic chunks
    semantic_chunks_data = prepare_chunks_for_ingestion(semantic_chunks)
    ingest_chunks_to_opensearch(client , index_name , semantic_chunks_data)



if __name__ == "__main__":

    # File location
    base_dir = "Files"
    pdf_file = "research_paper.pdf"
    pdf_file_path = f"{base_dir}/{pdf_file}"

    raw_chunks = partition_pdf(
        filename=pdf_file_path,
        strategy="hi_res",
        infer_table_structure=True,
        extract_image_block_types=["Image" , "Figure" , "Table"],      # We want to extract image figure and table from pdf
        extract_image_block_to_payload=True,
        chunking_strategy=None
    )

    processed_image = process_images_with_caption(raw_chunks=raw_chunks , use_gemini=True)
    
    processed_table = process_tables_with_description(raw_chunks=raw_chunks , use_gemini=False)

    text_chunks = partition_pdf(
        filename=pdf_file_path,
        strategy="hi_res",
        chunking_strategy="by_title",
        max_characters = 2000,
        combine_text_under_n_chars = 500,
        new_after_n_chars = 1500
    )

    semantic_chunks = create_semantic_chunks(text_chunks)
    
    index_name = "pdf_content_index"
    ingest_all_content_into_opensearch(processed_image , processed_table , semantic_chunks , index_name)