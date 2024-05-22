from vlite import VLite
from devon_agent.tool import Tool

class VLiteMemoryTool(Tool):
    def __init__(self, collection_name="devon_collection"):
        self.memory_manager = VLite(collection=collection_name)

    def __len__(self):
        return self.memory_manager.count()

    def add(self, text, metadata=None):
        result = self.memory_manager.add(data=text, metadata=metadata)
        self.memory_manager.save()  # Ensure data is saved after adding
        return result

    def retrieve(self, query_text, top_k=5, metadata=None, return_scores=False):
        return self.memory_manager.retrieve(text=query_text, top_k=top_k, metadata=metadata, return_scores=return_scores)

    def update(self, item_id, new_text=None, metadata=None, vector=None):
        return self.memory_manager.update(id=item_id, text=new_text, metadata=metadata, vector=vector)

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
        return list(self.memory_manager.dump().values())

    def get_entries_by_metadata(self, metadata):
        return self.memory_manager.get(where=metadata)

    def delete(self, item_ids):
        return self.memory_manager.delete(ids=item_ids)

    def save(self):
        self.memory_manager.save()

    def clear(self):
        self.memory_manager.clear()

    def info(self):
        self.memory_manager.info()