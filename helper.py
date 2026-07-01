#---------------------------------------------------------------------------------
#                                  Import Statements
#---------------------------------------------------------------------------------
from langchain_ollama import OllamaEmbeddings
from opensearchpy import OpenSearch

#---------------------------------------------------------------------------------
#                                   Logic Functions
#---------------------------------------------------------------------------------

def get_embedding(prompt):
    """
        Generate Embeddings of the data 
        Args:
            prompt(str) : Whatever data we want to convert into embedding
        Returns:
            return embeddings of given str
    """
    model = "nomic-embed-text"
    embeddings = OllamaEmbeddings(model=model)
    return embeddings.embed_query(prompt)


def get_opensearch_client(host,port):
    """
        Generating the Opensearch client and return to the user
        Args:
            host(str) : host name
            port(int) : port number
        Returns:
            OpenSearch client 
    """
    client = OpenSearch(
        hosts = [{"host" : host , "port" : port}],
        http_compress = True,
        timeout = 30,
        max_retries = 3,
        retry_on_timeout = True
    )

    if client.ping():
        print("Connected to OpenSearch...")

    return client 


#---------------------------------------------------------------------------------
#                                   Checking code
#---------------------------------------------------------------------------------

# if __name__ == "__main__":
#     # print(get_embedding("Paras Patel"))

#     print(len(get_embedding("hello")))