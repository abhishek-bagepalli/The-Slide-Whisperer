def chunk_text(text_list, min_chunk_size=1000, max_chunk_size=6000):
    """
    Chunk text into meaningful sections based on size and content.
    Handles both text strings and nested table data.
    
    Args:
        text_list (list): List of text strings and table data to chunk
        min_chunk_size (int): Minimum size of each chunk
        max_chunk_size (int): Maximum size of each chunk
        
    Returns:
        list: List of text chunks
    """
    chunks = []
    current_chunk = []
    current_size = 0
    
    for text_item in text_list:
        # Handle table data (nested lists)
        if isinstance(text_item, list):
            # Convert table rows to text
            table_text = []
            for row in text_item:
                if isinstance(row, list):
                    table_text.append(' | '.join(str(cell) for cell in row))
                else:
                    table_text.append(str(row))
            text_item = '\n'.join(table_text)
        
        # If single item is too large, split it into sentences
        if len(text_item) > max_chunk_size:
            sentences = text_item.split('. ')
            for sentence in sentences:
                if current_size + len(sentence) > max_chunk_size:
                    if current_chunk:
                        chunks.append(' '.join(current_chunk))
                        current_chunk = []
                        current_size = 0
                    if len(sentence) > max_chunk_size:
                        # If single sentence is too long, split it
                        words = sentence.split()
                        temp_chunk = []
                        temp_size = 0
                        for word in words:
                            if temp_size + len(word) + 1 <= max_chunk_size:
                                temp_chunk.append(word)
                                temp_size += len(word) + 1
                            else:
                                if temp_chunk:
                                    chunks.append(' '.join(temp_chunk))
                                temp_chunk = [word]
                                temp_size = len(word)
                        if temp_chunk:
                            chunks.append(' '.join(temp_chunk))
                    else:
                        chunks.append(sentence)
                else:
                    current_chunk.append(sentence)
                    current_size += len(sentence) + 1
        else:
            if current_size + len(text_item) > max_chunk_size:
                if current_chunk:
                    chunks.append(' '.join(current_chunk))
                current_chunk = [text_item]
                current_size = len(text_item)
            else:
                current_chunk.append(text_item)
                current_size += len(text_item) + 1
    
    # Add any remaining text
    if current_chunk:
        chunks.append(' '.join(current_chunk))
    
    # Filter out chunks that are too small
    chunks = [chunk for chunk in chunks if len(chunk) >= min_chunk_size]
    
    return chunks
