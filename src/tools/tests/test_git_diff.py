import dotenv
from tools.git import GitDiff
import instructor
import openai
dotenv.load_dotenv()

client = instructor.patch(openai.OpenAI())

# Response model with simple types like str, int, float, bool
resp = client.chat.completions.create(
    model="gpt-4.5-turbo",
    response_model=GitDiff,
    messages=[
        {
            "role": "system",
            "content": "Your job is to help fix code",
        },
        {
            "role": "user",
            "content": """
Describe the problem
create_batches function from utils is used to batch a large list of data into manageable batches. However, create_batches expects List as its input type which requires the entire data to be loaded in memory which is infeasible for large data, something, that batches would regularly handle.

Describe the proposed solution
create_batch should accept an Iterable type instead of lists so a lazily evaluated Iterable can be passed. def create_batches( api: BaseAPI, ids: IDs, embeddings: Optional[Embeddings] = None, metadatas: Optional[Metadatas] = None, documents: Optional[Documents] = None, ) -> List[Tuple[IDs, Embeddings, Optional[Metadatas], Optional[Documents]]]: could be changed to def create_batches( api: BaseAPI, ids: IDs, embeddings: Optional[Iterable[Embedding]] = None, metadatas: Optional[Iterable[Metadata]] = None, documents: Optional[Iterable[Document]] = None, ) -> List[Tuple[IDs, Embeddings, Optional[Metadatas], Optional[Documents]]]:

Alternatives considered
While calling the function, type checking can simply be ignored

Importance
nice to have

Additional Information
No response

from typing import Optional, Tuple, List

from chromadb.api import BaseAPI

from chromadb.api.types import (

Documents,

Embeddings,

IDs,

Metadatas,

)

def create_batches(

api: BaseAPI,

ids: IDs,

embeddings: Optional[Embeddings] = None,

metadatas: Optional[Metadatas] = None,

documents: Optional[Documents] = None,

) -> List[Tuple[IDs, Embeddings, Optional[Metadatas], Optional[Documents]]]:

_batches: List[

Tuple[IDs, Embeddings, Optional[Metadatas], Optional[Documents]]

] = []

if len(ids) > api.max_batch_size:

# create split batches

for i in range(0, len(ids), api.max_batch_size):

_batches.append(

( # type: ignore

ids[i : i + api.max_batch_size],

embeddings[i : i + api.max_batch_size] if embeddings else None,

metadatas[i : i + api.max_batch_size] if metadatas else None,

documents[i : i + api.max_batch_size] if documents else None,

)

)

else:

_batches.append((ids, embeddings, metadatas, documents)) # type: ignore

return _batches

only give git diffs for the change
""",
        },
    ],
)

print(resp)
