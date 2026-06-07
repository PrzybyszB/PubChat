from articles_parser import main as articles_parser
from embedding_processor import main as embedding_processor
from llm_processor import main as llm_processor

def run_pipeline():

    articles_parser()

    llm_processor()

    embedding_processor()

if __name__ == "__main__":
    run_pipeline()