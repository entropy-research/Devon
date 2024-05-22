from vlite import VLite
from devon_agent.tool import Tool

class VLiteMemoryTool(Tool):
    def __init__(self, collection_name="devon_collection"):
        self.memory_manager = VLite(collection=collection_name)

    def add(self, text, metadata=None):
        return self.memory_manager.add(text, metadata=metadata)

    def retrieve(self, query_text, top_k=5):
        return self.memory_manager.retrieve(text=query_text, top_k=top_k)

    def update(self, item_id, new_text):
        return self.memory_manager.update(id=item_id, text=new_text)
    
    def get_last_item(self, n=1):
        if not self.memory_manager.index or n <= 0:
            return None
        # Ensure that n does not exceed the number of items in the index
        if n > len(self.memory_manager.index):
            return None
        nth_last_chunk_id = list(self.memory_manager.index.keys())[-n]
        nth_last_item = self.memory_manager.index[nth_last_chunk_id]
        return {
            'id': nth_last_chunk_id,
            'text': nth_last_item['text'],
            'metadata': nth_last_item['metadata'],
            'binary_vector': nth_last_item['binary_vector']
        }
    
    def get_all_items(self):
        # Return all items sorted by their keys (assuming keys are added in chronological order)
        return [self.memory_manager.index[key] for key in sorted(self.memory_manager.index.keys())]

    def delete(self, item_id):
        return self.memory_manager.delete(ids=[item_id])

    def save(self):
        self.memory_manager.save()

    def load(self):
        self.memory_manager.load()