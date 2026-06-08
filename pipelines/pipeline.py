from pipelines.articles_parser import main as articles_parser
from pipelines.embedding_processor import main as embedding_processor
from pipelines.llm_processor import main as llm_processor

def run_pipeline():

    articles_parser()

    llm_processor()

    embedding_processor()

if __name__ == "__main__":
    run_pipeline()