#---------------------------------------------------------------------------------
#                                  Import Statements
#---------------------------------------------------------------------------------

import os,json 
import google.generativeai as genai 
import requests 
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from retrieval import hybrid_search,semantic_search,keyword_search
from langchain_ollama import ChatOllama
import traceback
# Load all Variables
load_dotenv()


#---------------------------------------------------------------------------------
#                                  main Logic Statements
#---------------------------------------------------------------------------------

# Getting gemini api from the env
gemini_api_key = os.getenv("GEMINI_API_KEY")
if not gemini_api_key:
    print("Error in getting gemini api key...")
else:
    print(f"Configuring Gemini with API key : {gemini_api_key[:5]}...")
    genai.configure(api_key=gemini_api_key)

# Define RAG Prompt
RAG_PROMPT_TEMPLATE = """
You are an expert AI assistant for Retrieval-Augmented Generation (RAG).

Answer ONLY using the provided context. If the answer is not in the context, say "I don't know based on the provided documents."

────────────────────
CONTEXT:
{context}

QUESTION:
{question}

────────────────────
RESPONSE STYLE:

Generate a well-structured, visually clean Markdown answer.

Use when helpful:
- Headings (##, ###)
- Bullet points
- Tables for comparisons
- Code blocks if needed
- Emojis sparingly for clarity (📌 💡 ⚠️ 📊 🚀)

Always keep responses:
- Clear and structured
- Fact-based (no hallucination)
- Easy to scan

Preferred structure (adapt as needed):

## 🎯 Answer
Direct response

## 📖 Explanation
Clear breakdown of the concept

## 📊 Key Insights
- Important points
- Observations

## ⚖️ Advantages vs Limitations (if applicable)
| Advantages | Limitations |
|------------|-------------|

## 🔍 Analysis (if applicable)
Short analytical perspective

## 📝 Summary
Concise final takeaway

────────────────────
Return ONLY Markdown.
"""

# Making prompt template from the RAG PROMPT TEMPLATE
prompt = PromptTemplate(
    input_variables=["context" , "question"],
    template=RAG_PROMPT_TEMPLATE
)

def generate_with_gemini(prompt_text , model_name ="gemini-2.5-flash" , stream=False):
    """
        Generate Response using Google's gemini model with error handling
        Args:
            prompt_text(str) : prompt need to resolve
            model_name(str) : By default it will be provided
            stream(bool) : For stream the output
        Returns:
            str : Generated response
    """
    try:
        # Init the model
        print("Initializing the Gemini Model...")
        model = genai.GenerativeModel(model_name=model_name)

        # Safety check for prompt length
        if len(prompt_text) > 30000:
            prompt_text = prompt_text[:30000] + "...[truncated due to length]"
            print(f"Warning : Prompt was truncated to 30000 characters.")

        # Setup Generation
        generation_config = {
            "temperature" : 0.7,
            "top_p" : 0.95,
            "top_k" : 40,
            "max_output_tokens" : 2048
        }

        # Configure safety settings to prevent blocking
        safety_settings = {
            "harassment" : "block_none",
            "hate" : "block_none",
            "sexual" : "block_none",
            "dangerous" : "block_none"
        }

        # Handle streaming vs non-streaming differently
        if stream:
            print("Starting streaming response generation...")
            response_generator = model.generate_content(
                contents=prompt_text,
                generation_config=generation_config,
                safety_settings=safety_settings,
                stream=True
            )

            # Process stream chunks 
            for chunk in response_generator:
                # Most direct way to get text from a chunk
                if hasattr(chunk , "text"):
                    if chunk.text: # only yield no-empty text
                        yield chunk.text 
                # Alternative way through parts
                elif hasattr(chunk,"parts"):
                    for part in chunk.parts:
                        if hasattr(part,"text") and part.text:
                            yield part.text 
            
        else:
            print("Requesting non-streaming response...")
            response = model.generate_content(
                contents=prompt_text,
                generation_config=generation_config,
                safety_settings=safety_settings,
            )

            # Extract text from response
            if hasattr(response , "text"):
                return response.text 
            elif hasattr(response,"parts") and response.parts:
                return "".join([p.text for p in response.parts if hasattr(p,"text")])
            else:
                return f"Response received but couldnot extract text : {str(response)}"
    
    except Exception as e:
        error_msg = f"Error with Gemini generation : {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        if stream:
            yield error_msg
        else:
            return error_msg
        


def generate_with_ollama(prompt_text,model_name="llama3:latest",stream=False):
    """
    Generate response using Ollama via LangChain ChatOllama.

    Args:
        prompt_text (str): input prompt
        model_name (str): local ollama model
        stream (bool): streaming or not

    Returns:
        str or generator (stream)
    """

    try:
        print("Initializing Ollama model...")

        llm = ChatOllama(
            model=model_name,
            temperature=0.7
        )

        # safety trim (same as your Gemini function)
        if len(prompt_text) > 30000:
            prompt_text = prompt_text[:30000] + "...[truncated]"
            print("Warning: prompt truncated to 30000 chars")

        # -----------------------
        # STREAM MODE
        # -----------------------
        if stream:
            print("Streaming response...")

            for chunk in llm.stream(prompt_text):
                if hasattr(chunk, "content") and chunk.content:
                    yield chunk.content

        # -----------------------
        # NON-STREAM MODE
        # -----------------------
        else:
            print("Generating response...")

            response = llm.invoke(prompt_text)

            return response.content if hasattr(response, "content") else str(response)

    except Exception as e:
        error_msg = f"Ollama error: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)

        if stream:
            yield error_msg
        else:
            return error_msg
        

def generate_rag_response(query , search_type = "hybrid" , top_k = 5, model_type = "gemini" , stream=False):
    """
        Generate RAG response using retrieved chunks.
        Args:
            query(str) : Query of user
            search_type(str) : which kind of search we want to perfom hybrid,semantic,keyword
            top_k(int) : top how many results
            model_type(str) : type of the model like gemini or ollama 
            stream(bool) : Wheather to stream the response 
        Returns:
            Generated response or generator for streaming
    """
    try:
        # Retrive relevant chunks based on search_type
        if search_type == "keyword":
            results = keyword_search(query , top_k)
        elif search_type == "semantic":
            results = semantic_search(query , top_k)
        else: # Hybrid
            results = hybrid_search(query , top_k)

        if not results:
            message = "No relevant information found. Please try a different search type or some other query."
            if stream:
                yield message
                return
            else:
                return message 
            
        # Format retrieved contexts
        contexts = [] 
        for i, hit in enumerate(results):
            source = hit['_source']
            content = source.get("content" , "")
            content_type = source.get("content_type" , "unknown")

            # Add metadata if available 
            metadata_info = ""
            if "metadata" in source and source['metadata']:
                if "caption" in source['metadata'] and source['metadata']['caption']:
                    metadata_info += f"\nCaption : {source['metadata']['caption']}"

            context_entry = (
                f"[Document : {i+1} - {content_type}] {metadata_info}\n{content}"
            )
            contexts.append(context_entry)

        # Format the prompt using Langchain prompt template
        context_text = "\n----\n".join(contexts)
        prompt_text = prompt.format(context=context_text , question = query)

        # Generate response with selected model
        if model_type == "gemini":
            if stream:
                yield from generate_with_gemini(prompt_text = prompt_text , stream=True)
            else:
                return generate_with_gemini(prompt_text = prompt_text,stream=False)
        else: # Ollama 
            if stream:
                yield from generate_with_ollama(prompt_text=prompt_text , stream=True)
            else:
                return generate_with_ollama(prompt_text=prompt_text , stream=False)
            
    except Exception as e:
        error_message = f"Error in RAG process : {str(e)}"
        if stream:
            yield error_message
        else:
            return error_message
        

#---------------------------------------------------------------------------------
#                                  Code checking 
#---------------------------------------------------------------------------------

# if __name__ == "__main__":
#     # Test both streaming and non-streaming
#     query = "How does RAG Work?"

#     # Test streaming
#     print("Response : " , end = "" , flush=True)
#     for chunk in generate_rag_response(query , "hybrid" , 3 , "ollama",True):
#         print(chunk,end="",flush=True)