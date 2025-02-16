import os
import pickle
import networkx as nx

def load_and_merge_graphs(pickles_dir):
    """
    Функция загрузки и объединения графов
    Входные параметры:
        > pickles_dir - директория с сохранёнными графами .pickle
    Возвращаемое значение:
        > merged_graph - объединенный граф
    """
    merged_graph = nx.Graph()
    # Перебираем все .pickle файлы в директории
    for file in os.listdir(pickles_dir):
        if file.endswith(".pickle"):
            file_path = os.path.join(pickles_dir, file)
            with open(file_path, 'rb') as fp:
                g: nx.Graph = pickle.load(fp)
                merged_graph = nx.compose(merged_graph, g)  # Объединяем графы
    return merged_graph