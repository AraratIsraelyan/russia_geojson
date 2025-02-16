"""
Тестирование алгоритмов поиска оптимальных путей
"""
import osmnx as ox
import pandas as pd
import networkx as nx
import multiprocessing as mp
import concurrent.futures
from tqdm.auto import tqdm
from modules import pickle_union as pu
from modules import context_timer as ct

import ride_pfa.clustering as cls
import ride_pfa.path_finding as pfa
import ride_pfa.centroid_graph.centroids_graph_builder as cgb



res_time = {}  # Определим пустой словарь для хранения времени выполнения
for key in ["AStar_nx", "Dijkstra_nx", "AStar_ride", "Dijkstra_ride", "BiDijkstra_ride", "AStar_ride_sub", "Dijkstra_ride_sub", "OSMNX"]:
    res_time[key] = []


def task(index):
    row = test_df.iloc[index]
    start_node = row["node_1"]
    end_node = row["node_2"]

    ### A* (networkx)
    with ct.timer() as elapsed_time:
        nx.astar_path(g, start_node, end_node, heuristic=heuristic, weight='weight')
    res_time['AStar_nx'].append(f"{index}:{elapsed_time()}")

    ### Дийкстра (networkx)
    with ct.timer() as elapsed_time:
        nx.dijkstra_path(g, start_node, end_node, weight='weight')
    res_time['Dijkstra_nx'].append(f"{index}:{elapsed_time()}")

    ### A* (ride)
    with ct.timer() as elapsed_time:
        astar_algo.find_path(start_node, end_node)
    res_time['AStar_ride'].append(f"{index}:{elapsed_time()}")

    ### Дийкстра (ride)
    with ct.timer() as elapsed_time:
        dijkstra_algo.find_path(start_node, end_node)
    res_time['Dijkstra_ride'].append(f"{index}:{elapsed_time()}")

    ### Дийкстра (ride)
    with ct.timer() as elapsed_time:
        bidijkstra_algo.find_path(start_node, end_node)
    res_time['BiDijkstra_ride'].append(f"{index}:{elapsed_time()}")

    ### A* (Центроидный граф > субоптимальный алгоритм)
    with ct.timer() as elapsed_time:
        suboptimal_algorithm_Astar.find_path(start_node, end_node)
    res_time['AStar_ride_sub'].append(f"{index}:{elapsed_time()}")

    ### Дийкстра (Центроидный граф > субоптимальный алгоритм)
    with ct.timer() as elapsed_time:
        suboptimal_algorithm_Dijkstra.find_path(start_node, end_node)
    res_time['Dijkstra_ride_sub'].append(f"{index}:{elapsed_time()}")

    ### OSMNX
    # Рассчитайте кратчайший путь и расстояние между точками
    with ct.timer() as elapsed_time:
        ox.routing.shortest_path(g, start_node, end_node, weight='length')
    res_time['OSMNX'].append(f"{index}:{elapsed_time()}")
    return 0


if __name__ == '__main__':

    """ 
    Создание графа дорожной сети на основе объединенного графов дорог МО и Москвы
    ### Graph with 177143 nodes and 228969 edges
    """
    save_dir = r"graphs"
    with ct.timer() as elapsed_time:
        g = pu.load_and_merge_graphs(pickles_dir=save_dir)
    print(f"Построение графа выполнено за:  {elapsed_time():.4f},   |   {g}", end="\n\n")



    """
    Считываем датафрейм со сгенерированными нодами
    """
    test_df = pd.read_excel("Сгенерированный_датафрейм_1000нод.xlsx", engine="openpyxl")
    print(test_df.head(4), end="\n\n")


    def heuristic(u, v):
        u = g.nodes[u]
        v = g.nodes[v]
        return ((u['x'] - v['x']) ** 2 + (u['y'] - v['y']) ** 2) ** 0.5


    """
    RIDE: кластеризация, поиск центроидов
    """
    # cms_resolver: Объект для кластеризации
    cms_resolver = cls.LouvainCommunityResolver(resolution=1)
    # Строим центроидный граф для использования в субоптимальном алгоритме (экономия памяти)
    cg = cgb.CentroidGraphBuilder().build(g, cms_resolver)
    # Создаем субоптимальный алгоритм поиска пути
    suboptimal_algorithm_Dijkstra = pfa.ExtractionPfa(
        g=g,
        upper=pfa.Dijkstra(cg.g),
        down=pfa.Dijkstra(g),
        cluster="cluster"
    )
    # Создаем субоптимальный алгоритм поиска пути
    suboptimal_algorithm_Astar = pfa.ExtractionPfa(
        g=g,
        upper=pfa.AStar(cg.g),
        down=pfa.AStar(g),
        cluster="cluster"
    )
    dijkstra_algo = pfa.Dijkstra(g)
    bidijkstra_algo = pfa.BiDijkstra(g)
    astar_algo = pfa.AStar(g)

    """
    Используем многопоточность для выполнения теста
    Каждая итерация будет использовать свой поток
    """
    with concurrent.futures.ThreadPoolExecutor() as executor:
        executor.map(task, range(len(test_df)))
    # with mp.Pool(mp.cpu_count()) as pool:
    #     _ = pool.starmap(task, [(i, test_df) for i in range(len(test_df))])

    print(res_time)
    with open("file.txt", "w") as output:
        output.write(str(res_time))

    # Функция для парсинга значений
    def parse_results(results):
        parsed = []
        for algo, values in results.items():
            for entry in values:
                index, time = entry.split(":")
                parsed.append({"index": int(index), "algorithm": algo, "time": float(time)})
        return parsed

    # Преобразуем словарь res_time в DataFrame
    df = pd.DataFrame(parse_results(res_time))
    # Сохраняем DataFrame в Excel-файл
    output_file = "results.xlsx"
    df.to_excel(output_file, index=False)
    print(f"Результаты сохранены в файле '{output_file}'.")