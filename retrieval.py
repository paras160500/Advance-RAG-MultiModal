#---------------------------------------------------------------------------------
#                                  Import Statements
#---------------------------------------------------------------------------------
from helper import get_embedding, get_opensearch_client
from pprint import pprint

#---------------------------------------------------------------------------------
#                              Logic function Statements
#---------------------------------------------------------------------------------

def keyword_search(query_text , top_k = 10):
    """
        Perform a keyword search using OpenSearch
        Args:
            query_text(str) : The query user will pass for search
            top_k(int) : number of results
        Returns:
            list of search results
    """
    # Setting up client and index_name
    client = get_opensearch_client("localhost" , 9200)
    index_name = "pdf_content_index"

    try:
        # Create Keyword searh query
        search_query = {
            "size" : top_k,
            "query" : {"match" : {"content" : query_text}},
            "_source" : ["content" , "content_type"]
        }
        # search across the database
        response = client.search(index = index_name , body=search_query)
        return response['hits']['hits']
    except Exception as e:
        print(f"Keyword Search error : {str(e)}")
        return []



def semantic_search(query_text , top_k = 10):
    """
        Perform a semantic search using vector embeddings
        Args:
            query_text(str) : user query
            top_k(int) : number of results 
        Returns:
            List of search results
    """ 
    # Setting up client and index_name
    client = get_opensearch_client("localhost" , 9200)
    index_name = "pdf_content_index"

    try:
        query_embedding = get_embedding(query_text)

        # Create a Semantic Search query
        search_query = {
            "size" : top_k,
            "query" : {
                "knn" : {
                    "embedding" : {
                        "vector" : query_embedding,
                        "k" : top_k
                    }
                }
            },
            "_source" : ["content" , "content_type"]
        }
        # search across the database
        response = client.search(index = index_name , body=search_query)
        return response['hits']['hits']
    except Exception as e:
        print(f"Semantic Search error : {str(e)}")
        return []
    

def hybrid_search(query_text , top_k = 10):
    """
        Perform a hybird search using vector embeddings
        Args:
            query_text(str) : user query
            top_k(int) : number of results 
        Returns:
            List of search results
    """ 
    # Setting up client and index_name
    client = get_opensearch_client("localhost" , 9200)
    index_name = "pdf_content_index"

    try:
        # Get embeddings of the query
        query_embeddings = get_embedding(query_text)

        # Create a hybrid search query
        search_query = {
            "size" : top_k,
            "query" : {
                "bool" : {
                    "should" : [
                        {"knn" : {"embedding" : {"vector" : query_embeddings , "k" : top_k}}},
                        {"match" : {"content" : query_text}}
                    ]
                }
            },
            "_source" : ["content" , "content_type"]
        }
        # search across the database
        response = client.search(index = index_name , body=search_query)
        return response['hits']['hits']
    except Exception as e:
        print(f"Hybrid search fail...Trying Fallback search ... ")
        try:
            fallback_query = {
                "size" : top_k,
                "query" : {"match" : {"content" : query_text}},
                "_source" : ["content" , "content_type"]
            }
            response = client.search(index = index_name , body=fallback_query)
            return response['hits']['hits']
        except Exception as e:
            print(f"Semantic Search error : {str(e)}")
            return []

#---------------------------------------------------------------------------------
#                              Code checking block
#---------------------------------------------------------------------------------

# if __name__ == "__main__":
#     query = "Compare RAG v/s Fine-tuning"
#     # results = keyword_search(query)
#     # results = semantic_search(query)
#     results = hybrid_search(query)
#     pprint(results)