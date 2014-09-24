#!/usr/bin/python

import networkx as nx, sys, os, scipy.io
from hotnet2 import hnap

def get_parser():                                                             
    description = 'Creates a heat diffusion influence matrix from an input graph.'
    parser = hnap.HotNetArgParser(description=description, fromfile_prefix_chars='@')
    parser.add_argument('-e', '--input_edgelist', required=True, help='Input edge list.')
    parser.add_argument('-i', '--gene_index_file', required=True, help='Input gene index file.')
    parser.add_argument('-o', '--output_dir', required=True, help='Path to output dir.')
    parser.add_argument('-p', '--prefix', required=True, help='Output prefix.')
    parser.add_argument('-s', '--start_index', default=1, type=int, help='Start index.')
    parser.add_argument('-t', '--time', required=True, type=float, help='Diffusion time.')
    return parser                                                               

def run(args):
    # Load input graph
    print "* Loading input graph..."
    G = nx.Graph()
    G.add_edges_from([map(int, l.rstrip().split()[:2]) for l in open(args.input_edgelist)])
    print "\t{} nodes with {} edges".format(len(G.nodes()), len(G.edges()))

    # Remove self-loops, zero degree nodes, and
    # restricting to the largest connected component
    print "* Removing self-loops, zero degree nodes, and ",
    print "restricting to the largest connected component"
    G.remove_edges_from([(u,v) for u, v in G.edges() if u == v])
    G.remove_nodes_from([n for n in G.nodes() if G.degree(n) == 0])
    G = G.subgraph(sorted(nx.connected_components( G ), key=lambda cc: len(cc), reverse=True)[0])

    print "\t{} nodes with {} edges remaining".format(len(G.nodes()), len(G.edges()))

    # Load gene index
    arrs = [l.rstrip().split() for l in open(args.gene_index_file)]
    index2gene = dict([(int(arr[0]), arr[1]) for arr in arrs])

    # Compute and save Laplacian
    os.system( 'mkdir -p ' + args.output_dir )
    print "* Computing Laplacian..."
    L = nx.laplacian_matrix(G)
    scipy.io.savemat("{}/{}_laplacian.mat".format(args.output_dir, args.prefix),
                     dict(L=L),oned_as='column')

    # Exponentiate the Laplacian for the given time and save it
    from scipy.linalg import expm
    Li = expm( -args.time * L )
    scipy.io.savemat("{}/{}_inf_{}.mat".format(args.output_dir, args.prefix, args.time),
                     dict(Li=Li), oned_as='column')

    # Save the index to gene mapping
    index_output_file = "{}/{}_index_genes".format(args.output_dir, args.prefix)
    nodes = G.nodes()
    gene_index_output = ["{} {}".format(i + args.start_index, index2gene[nodes[i]])
                         for i in range(len(nodes))]
    open(index_output_file, "w").write("\n".join(gene_index_output))

    # Create edge list with revised indices
    edge_indices = []
    for u, v in G.edges():
        i = nodes.index(u) + args.start_index
        j = nodes.index(v) + args.start_index
        edge_indices.append( sorted([i, j]) )
    edge_output_file = "{}/{}_edge_list".format(args.output_dir, args.prefix)
    edge_output = ["{} {} 1".format(u, v) for u, v in edge_indices]
    open(edge_output_file, "w").write( "\n".join(edge_output) )

if __name__ == "__main__":
    run(get_parser().parse_args(sys.argv[1:]))