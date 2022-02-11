from builtins import dict, print
import sys
import re
import networkx as nx
from itertools import combinations

from numpy import gradient

"""
Dataset ottenuto dalla query:

(SON[Title/Abstract] AND ("DNA-Binding Proteins"[Mesh] OR "RNA-Binding Proteins"[Mesh]) AND "SON protein, human"[nm]) OR "SON gene"[All Fields] OR "SON protein"[All Fields]\
OR NREBP[Title/Abstract]\
OR ("DBP-5"[Title/Abstract] AND "DNA-Binding Proteins"[MeSH])\
OR "NRE-Binding Protein"[Title/Abstract]\
OR KIAA1019[Title/Abstract]\
OR C21orf50[Title/Abstract]\
OR (SON3[Title/Abstract] AND "DNA-Binding Proteins"[MeSH])\
OR DBP5[Title/Abstract]'
"""


def parse_dataset(datasetPath : str) -> dict:
    
    articlesStr : list[str] = []
    
    with open(datasetPath,'r') as file:
        articlesStr = list(map(lambda x: x.replace('\n      ', ' '), file.read().split("\n\n")))

    dict = {}
    for art in articlesStr:

        # PubMed ID
        match = re.search('^PMID- (.*)$', art, re.MULTILINE)
        if match is None:
            continue
        pmid = match.group(1)

        # Title
        match = re.search('^TI  - (.*)$', art, re.MULTILINE)
        if match is None:
            continue
        ti = match.group(1)

        # Abstract
        match = re.search('^AB  - (.*)$', art, re.MULTILINE)
        if match is None:
            continue
        ab = match.group(1)

        # NLM Medical Subject Headings (MeSH) controlled vocabulary
        mh = re.findall('^MH  - (.*)$', art, re.MULTILINE)
        
        # Includes chemical, protocol or disease terms. May also a number assigned by the Enzyme Commission or by the Chemical Abstracts Service.
        rn = re.findall('^RN  - (.*)$', art, re.MULTILINE)

        # Non-MeSH subject terms (keywords) either assigned by an organization identified by the Other Term Owner, or generated by the author and submitted by the publisher
        ot = re.findall('^OT  - (.*)$', art, re.MULTILINE)

        dict[pmid] = {'Title' : ti, 'Abstract' : ab, 'MeSH' : mh, 'RNnumber': rn, 'OtherTerm': ot }

    return dict

def extract_mesh(articles : dict) -> set:
    mesh_terms = set()
    for art in articles.values():
        local_mesh = art.get('MeSH')
        if local_mesh is not None:
            mesh_terms.update(local_mesh)
    return mesh_terms


def build_cooccurrences_graph(articles : dict, mh = True, rn = True, ot = True, check_tags=[]) -> nx.Graph:
    graph = nx.Graph()

    for art in articles.values():
        terms = []
        if mh:
            terms += art.get('MeSH')
        if rn:
            terms += art.get('RNnumber')
        if ot:
            terms += art.get('OtherTerm')
        
        terms = list(filter(lambda x: x not in check_tags, terms))
        
        if not terms:
            continue
        
        for a, b in list(combinations(terms, 2)):
            if not graph.has_node(a):
                graph.add_node(a)
            if not graph.has_node(b):
                graph.add_node(b)
            
            if graph.has_edge(a, b):
                graph[a][b]['weight'] += 1
            else:
                graph.add_edge(a, b, weight=1)
    
    return graph
        

def main():

    if(len(sys.argv) < 2):
        print("Usage: $ python3", sys.argv[0], "<path_dataset_pubmed>")
        return
    path = sys.argv[1]

    articles : dict = parse_dataset(path)
    print('Numero di articoli: ', len(articles.keys()))

    #mesh_terms : set = extract_mesh(articles)
    #print('Numero di MeSH diversi: ', len(mesh_terms))

    ct = ['Humans', 'Animals']

    cooccurrences_graph = build_cooccurrences_graph(articles, check_tags=ct, ot=False)
    print('Grafo delle co-occorrenze:\n\tNodi: ', len(cooccurrences_graph.nodes), '\n\tArchi: ', len(cooccurrences_graph.edges))

    cooccurrences_list = list(cooccurrences_graph.edges.data('weight'))

    cooccurrences_list.sort(key = lambda x:x[2], reverse=True)
    
    with open('cooccurrences.txr', 'w') as file:
        for (u, v, wt) in cooccurrences_list:
            file.write(f"<<{u}>>\t<<{v}>>\t<<{wt}>>\n")

    print('Il grafo ha: ', nx.number_connected_components(cooccurrences_graph), ' componenti connesse')

    print('Coefficiente di clustering: ', nx.average_clustering(cooccurrences_graph))

    print('Diametro: ', nx.diameter(cooccurrences_graph))


if __name__ == "__main__":
    main()
    
    
    








