import numpy as np
from TNPA_Graph import *
from copy import deepcopy
import multiprocessing as mp
import matplotlib.pyplot as plt
import networkx as nx
import matplotlib.pyplot as plt

'''
对应Graph的1.0版。
调整MCMC为SIR特供版
'''

def plot(t_max,data,label):
    plt.plot(range(t_max+1), data  , label = label)

def read_all(epar,graph,time):
    MC = read_data(epar+graph+'_MCMC_'+time)
    PA = read_data(epar+graph+'_PA_'+time)
    DMP = read_data(epar+graph+'_DMP_'+time)
    TNPA = [read_data(epar+graph+'_TNPA_R='+str(r)+'_N='+str(R)+time) for r in range(3,R+1)]
    return [MC,PA,DMP,TNPA]

def read_data(filename):
    marginal_all = []
    average = [[],[],[]]
    with open(filename + '.txt','r') as f:
        line = f.readline()
        while line:
            if 'point' in line: # 点
                marginal_all.append([[],[],[]])
                f.readline() # S
                data = ''
                line = f.readline()
                lines = 0
                while line[:-1] not in 'SIR':
                    data += line[:-1]
                    line = f.readline() # I
                    lines += 1
                data = list(map(float, data.split(',')))
                marginal_all[-1][0] = data

                data = ''
                line = f.readline()
                for _ in range(lines):
                    data += line[:-1]
                    line = f.readline()
                data = list(map(float, data.split(',')))
                marginal_all[-1][1] = data

                data = ''
                line = f.readline()
                for _ in range(lines):
                    data += line[:-1]
                    line = f.readline()
                data = list(map(float, data.split(',')))
                marginal_all[-1][2] = data
                
            elif 'average' in line: #均值
                f.readline() # S
                data = ''
                line = f.readline()
                for _ in range(lines):
                    data += line[:-1]
                    line = f.readline() # I
                data = list(map(float, data.split(',')))
                average[0] = data

                data = ''
                line = f.readline()
                for _ in range(lines):
                    data += line[:-1]
                    line = f.readline()
                data = list(map(float, data.split(',')))
                average[1] = data

                data = ''
                line = f.readline()
                for _ in range(lines):
                    data += line[:-1]
                    line = f.readline()
                data = list(map(float, data.split(',')))
                average[2] = data
    return [np.array(marginal_all),np.array(average)]

def MCMC(para): 
    [repeats,epar,n,t_max,seed,spt,init_state,adjacency_matrix] = para
    marginal_sum = np.zeros([t_max+1,n,3])
    np.random.seed(seed)
    marginal_sum[0] = init_state*repeats

    for _ in range(repeats):
        marginal = init_state.copy()
        for t in range(1,t_max+1):
            for __ in range(spt):
                rand = np.random.rand(n)
                # infect = []
                # recover = []
                # for i in range(n):
                #     if marginal[i,0] == 1 and rand[i] < epar[0]*sum(marginal[neighs[i],1]):
                #         infect.append(i)
                #     elif marginal[i,1] == 1 and rand[i] <epar[1]:
                #         recover.append(i)
                infect_prob = epar[0] * adjacency_matrix@marginal[:,1]
                infect = (marginal[:, 0] == 1) & (rand < infect_prob)
                recover = (marginal[:, 1] == 1) & (rand < epar[1])
                marginal[infect,0] = 0
                marginal[infect,1] = 1
                marginal[recover,1] = 0
                marginal[recover,2] = 1
            marginal_sum[t] += marginal
    return marginal_sum

class Epidemic:
    '''
    Tensor Network Pair Approximation
    '''
    def __init__(self,g,gtype,etype,epar,tau,label = False):
        self.G = deepcopy(g)
        self.tau = tau
        self.name = etype + '_' + str(epar) +'_'+ gtype
        if label != False:
            self.name += '_' + str(label)
        self.etype = etype
        self.d = len(set(etype)) # 我可真是个小天才，笑

        self.n = len(g)
        self.marginal_all = []
        self.marginal = np.zeros((self.n,self.d))
        self.algorithm_label = ''

        self.epar = np.array(epar)*tau
        self.l = self.epar[0]
        self.r = self.epar[1]     
        
    def sys_init(self,info,init_type = 'single'):
        self.marginal[:,0] += 1
        if init_type == 'single':
            self.p = False
            self.marginal[info,0] = 0
            self.marginal[info,1] = 1
            self.name += '_single_ini=' + str(info) + '_'
        self.marginal_all.append(self.marginal.copy())
        self.edges = np.array(self.G.edges)

    def TNPA_init(self, partition, label, eps = 1e-7):
        self.PA_init()
        self.algorithm = 'TNPA'
        self.algorithm_label += label

        self.Regions = []
        self.TN = []
        for region in partition:
            self.Regions.append(region.graph)
            if region.subg:
                self.TN.append(Large_region(region,self.etype,self.epar,self.marginal,self.d,eps))
            else:
                self.TN.append(Small_region(region,self.etype,self.epar,self.marginal[list(region.graph)],self.d,eps))

        neighs_of_region = []

        for region in self.Regions:
            nodes = list(region)
            neighs = []
            for i in nodes:
                neigh = []
                for j in self.G[i]:
                    if j not in nodes:
                        neigh.append(j)
                neighs.append(neigh)
            neighs_of_region.append(neighs)
        
        self.neighs_of_region = neighs_of_region # 正序的指标含义[区块序号，点，点的邻居]
        [self.edges,self.PA_nodes] = self.get_PA_part() # 去除TN内边的其他边
        self.num_tn = len(partition)
        
    def get_PA_part(self):
        leftg = self.G.copy()
        out_g = self.G.copy()
        for Region_graph in self.Regions:
            leftg.remove_edges_from(Region_graph.edges())
            out_g.remove_nodes_from(list(Region_graph))
        edges = np.array(leftg.edges)
        nodes = list(out_g)
        return [edges,nodes]

    def PA_init(self): 
        self.algorithm = 'PA'
        self.IS = np.zeros((self.n,self.n))
        self.SS = np.zeros((self.n,self.n))
        for [i,j] in self.edges:
            self.IS[i,j] = self.marginal[i,1]*self.marginal[j,0]  # IS(i,j) = P(I_i,S_j)
            self.IS[j,i] = self.marginal[j,1]*self.marginal[i,0]
            self.SS[i,j] = self.marginal[i,0]*self.marginal[j,0]
            self.SS[j,i] = self.marginal[i,0]*self.marginal[j,0]
        
    def DMP_init(self):
        self.algorithm = 'DMP'
        self.H = np.ones((self.n,self.n))
        self.z = self.marginal[:,0].copy()
        self.K = np.zeros((self.n))
        self.k = np.zeros((self.n))

    def MCMC(self, init, t, repeats, mp_num = 10): # 默认开十个线程
        self.algorithm = 'MCMC'
        self.algorithm_label = '_repeats=' + str(repeats)
        # 替代sys_init 和update_to
        self.t = t 
        self.name += '_single_ini=' + str(init) + '_'
        self.name += self.algorithm + self.algorithm_label
        self.name += '_T=' + str(t) + '_tau=' + str(self.tau)

        self.marginal_all = np.zeros([t+1,self.n,self.d])
        init_state = np.zeros([self.n,3])
        init_state[:,0] = 1
        init_state[init,0] = 0
        init_state[init,1] = 1

        adjacency_matrix = nx.to_numpy_array(self.G)
        single_repeat = repeats//mp_num
        spt = int(1/self.tau) # steps per unit time

        # c1,c2 = mp.Pipe()
        # process_list = [mp.Process(target = MCMC, args = (c1,[single_repeat,self.epar,self.n,t,seed,spt,init_state,adjacency_matrix])) for seed in range(mp_num)]
        # [mc.start() for mc in process_list] 
        # for _ in range(mp_num):
        #     self.marginal_all += c2.recv()
        # self.marginal_all /= self.repeats
        # [p.join() for p in process_list]

        with mp.Pool(mp_num) as pool:
            arg_list = [
                [single_repeat,self.epar,self.n,t,seed,spt,init_state,adjacency_matrix]
                    for seed in range(mp_num)
                ]
            results = pool.map(MCMC,arg_list)
        for result in results:
            self.marginal_all += result
        self.marginal_all /= repeats
        # print(self.marginal_all)

    def update_to(self,t):
        self.t = t
        self.name += self.algorithm + self.algorithm_label
        self.name += '_T=' + str(t) + '_tau=' + str(self.tau)

        if self.algorithm == 'MCMC':
            print("MCMC don't need this function, try Epidemic.MCMC")

        else:
            pt = 0
            for _ in range(t):
                for __ in range(int(1/self.tau)):
                    self.update(pt)
                    pt += self.tau
                self.marginal_all.append(self.marginal.copy())
            self.marginal_all = np.array(self.marginal_all)

    def update(self,t):
        '''
        Under this code, only the pair posibility inside triangle was calculated with TN, and all other things keeps in PA 
        '''
        # t = time.time()
        if self.algorithm == 'TNPA':
            self.update_TN() # 先用前一步的信息更新TN，但先不更新TN缩并后的信息
            self.update_PA() # 再用PA更新TN以外的边
            self.contractTN() # 最后缩并TN，更新TN内部的边和点
            # print(self.IS)

        elif self.algorithm == 'PA':
            self.update_PA()

        elif self.algorithm == 'DMP':
            self.update_DMP(t)
        # print('one step time:',time.time()-t)

    def update_TN(self):
        for i in range(self.num_tn):
            nodes = list(self.Regions[i])
            neighs = self.neighs_of_region[i]
            msgin_all = []
            for j in range(len(nodes)):
                msgin = 0
                if len(neighs[j])>0 and self.marginal[nodes[j],0] > 0: # 有在外面的邻居，且由非零的marginal才有计算的意义
                    msgin = sum(self.IS[neighs[j],nodes[j]])/self.marginal[nodes[j],0]
                msgin_all.append(msgin)
            self.TN[i].update(np.array(msgin_all))
    
    def update_PA(self):
        new_IS = self.IS.copy()
        new_SS = self.SS.copy()

        for [a,b] in self.edges:

            [sa,sb] = [0,0]
            if self.marginal[a,0] != 0 :
                sa = (sum(self.IS[:, a]) - self.IS[b, a])/self.marginal[a,0]
            if self.marginal[b,0] != 0 :
                sb = (sum(self.IS[:, b]) - self.IS[a, b])/self.marginal[b,0]
                

            da = self.l* self.SS[a,b] * sa
            db = self.l* self.SS[a,b] * sb
            new_SS[a, b] -= (da+db)
            new_SS[b, a] = new_SS[a, b]
                
            new_IS[a, b] += (-( self.r + self.l * (1+sb) )* self.IS[a, b] + da)
            new_IS[b, a] += (-( self.r + self.l * (1+sa) )* self.IS[b, a] + db)
        
        self.update_marginal(self.IS)
        self.IS = new_IS
        # print(self.IS[:,1])
        self.SS = new_SS

    def contractTN(self): 
        for i in range(self.num_tn):
            nodes = list(self.Regions[i])
            l = len(nodes)
            for j in range(l):
                self.marginal[nodes[j]] = self.TN[i].marginal(j)                            
        # print(self.IS[:,1])
    
    def update_DMP(self,t):
        new_H = self.H.copy()

        for [a,b] in self.edges:
            # print( self.l,self.z[a],np.prod(self.H[:,a]))
            new_H[a, b] += -( self.r + self.l) * self.H[a,b] + self.r  + self.l*self.z[a]*np.prod(self.H[:,a])/self.H[b,a]
            new_H[b, a] += -( self.r + self.l) * self.H[b,a] + self.r  + self.l*self.z[b]*np.prod(self.H[:,b])/self.H[a,b]

        for i in list(self.G):
            s = self.z[i]*np.prod(self.H[:,i]) # x下一步的P(S)，但是上一步的还有用，先不更新
            self.k[i] += -self.r*self.k[i] + self.r*(s-self.marginal[i,0])/self.tau
            self.K[i] += self.tau*self.k[i]
            self.marginal[i,2] = (1-self.z[i])*(1-np.exp(-self.r*t/self.tau)) - self.K[i] 
            self.marginal[i,0] = s
            self.marginal[i,1] = 1.-self.marginal[i,0]-self.marginal[i,2]
        self.H = new_H

    def update_marginal(self,infc):
        if self.algorithm == 'TNPA':
            nodes = list(self.PA_nodes)
        else:
            nodes = list(self.G)
        for j in nodes:
            delta = np.zeros([self.d])
            deltai = self.l * sum(infc[:,j]) # delta with symbol x will add on the marginal of x 
            delta[:2] += [-deltai, deltai]

            deltar = self.r * self.marginal[j,1]
            delta += [0, - deltar, deltar]
            self.marginal[j] += delta

    def save_data(self, precision, form = 'all'):
        marginal_all = np.round(self.marginal_all,precision)
        f = open(self.name + '.txt','w')
        state = 'SIR'[:self.d]

        if form != 'ave':
            for i in range(self.n):
                f.write(str(i)+'th point \n')
                for j in range(self.d):
                    f.write(state[j]+'\n')
                    for t in range(self.t+1):
                        f.write(str(marginal_all[t,i,j]))
                        if t != self.t:
                            f.write(',')
                        if (t+1) % 20 == 0:
                            f.write('\n')
                    f.write('\n')
        
        if form != 'node_only':
            f.write('in average \n')
            ave = np.round(np.average(marginal_all, axis=1),precision)
            for j in range(self.d):
                f.write(state[j]+'\n')
                for t in range(self.t+1):
                    f.write(str(ave[t,j]))
                    if t != self.t:
                        f.write(',')
                    if (t+1) % 20 == 0:
                        f.write('\n')
                f.write('\n')
        
        f.close()

    def save_error(self, marginal_MC, precision):
        error_all = np.round(np.abs(self.marginal_all-marginal_MC),precision)
        f = open(self.name + '_error.txt','w')
        state = 'SIR'[:self.d]

        for i in range(self.n):
            f.write(str(i)+'th point \n')
            for j in range(self.d):
                f.write(state[j]+'\n')
                for t in range(self.t+1):
                    f.write(str(error_all[t,i,j]))
                    if t != self.t:
                        f.write(',')
                    if (t+1) % 20 == 0:
                        f.write('\n')
                f.write('\n')
    
        f.write('in average \n')
        ave = np.round(np.average(error_all, axis=1),precision)
        for j in range(self.d):
            f.write(state[j]+'\n')
            for t in range(self.t+1):
                f.write(str(ave[t,j]))
                if t != self.t:
                    f.write(',')
                if (t+1) % 20 == 0:
                    f.write('\n')
            f.write('\n')
        
        f.close()

    def save_snap(self, t, precision):
        marginal_t = np.round(self.marginal_all[t],precision)
        f = open(self.name + 'snap_at_t=' + str(t) + '.txt','w')
        state = 'SIR'[:self.d]

        for j in range(self.d):
            f.write(state[j]+'\n')
            f.write(str(marginal_t[:,j]))
            f.write('\n')
        
        
        f.close()

class Small_region:
    def __init__(self,G,etype,epar,init,d,eps):
        self.G = G.graph
        self.nodes = list(self.G)
        self.n = len(self.nodes)
        self.l = epar[0]
        self.r = epar[1]
        self.d = d
        self.eps = eps

        t = init[0]
        for node in range(1,self.n):
            t = np.outer(t,init[node]).reshape(-1)
        self.T = t.reshape([self.d for _ in range(self.n)])
        self.get_operators(etype)

    def get_operators(self,etype): #后面写成左乘了，所以算符的后指标是初态
        infc = np.eye(self.d**2).reshape(self.d,self.d,self.d,self.d)
        infc[1,1,0,1] += self.l
        infc[0,1,0,1] -= self.l
        infc[1,1,1,0] += self.l
        infc[1,0,1,0] -= self.l
        self.infc = infc.reshape(self.d*self.d,self.d*self.d)
        # print(self.infc)
        getinfc = np.zeros([self.d,self.d])
        getinfc[1,0] += self.l
        getinfc[0,0] -= self.l
        self.getinfc = getinfc

        local = np.eye(self.d)
        local[2,1] += self.r
        local[1,1] -= self.r

        self.local = local
        # print(local)
        
    def update(self,msgin):
        t = self.T
        for edge in list(self.G.edges()): #内部的感染
            [a,b] = edge
            i = self.nodes.index(a)
            j = self.nodes.index(b)
            if j<i:
                [i,j] = [j,i]
            t = np.swapaxes(np.swapaxes(t,i,0),j,1)
            t = t.reshape(self.d*self.d,-1)
            t = self.infc @ t
            t = t.reshape([self.d for _ in range(self.n)])
            t = np.swapaxes(np.swapaxes(t,j,1),i,0)

        for i in range(self.n): # 外部的感染和各点的康复/恢复易染
            t = np.swapaxes(t,i,0)
            t = t.reshape(self.d,-1)
            t = self.local @ t
            if abs(msgin[i])>self.eps:
                t = (np.eye(self.d)+msgin[i]*self.getinfc) @ t
            t = t.reshape([self.d for _ in range(self.n)])
            t = np.swapaxes(t,i,0)

        self.T = t

    def marginal(self,i):
        marginal = np.sum(self.T,axis = tuple([dim for dim in range(self.n) if (dim != i)]))
        return marginal

class Large_region:
    def __init__(self,region:region_graph,etype,epar,init,d,eps):
        self.nodes = list(region.graph)
        self.subgnum = region.n_sg
        self.subregions = []
        self.macro_g = region.macro_g
        # print(list(region.macro_g),list(region.macro_g.edges()))
        self.gid = []
        # print(region.boundaries)
        for i in range(0,self.subgnum):
            self.subregions.append(subregion(region.subregions[i],region.boundaries[i],etype,epar,init[list(region.subregions[i])],d,eps))
            self.gid.append([])
            for node in list(region.subregions[i]):
                self.gid[-1].append(self.nodes.index(node))

    def update(self,msgin):
        o_in = [[None for _ in range(self.subgnum)] for _ in range(self.subgnum)]
        o_out = [[None for _ in range(self.subgnum)] for _ in range(self.subgnum)]
        
        for i in range(len(self.subregions)):
            subg = self.subregions[i]
            o_out[i] = subg.o_out()

        # 由于list不能按维度索引的问题，只能手动做转置
        for i in range(self.subgnum):
            for j in range(self.subgnum):
                o_in[i][j] = o_out[j][i]
                
        for i in range(len(self.subregions)):
            subg = self.subregions[i]
            subg.update(msgin[self.gid[i]],o_in[i])
        
    def marginal(self,i):
        n1 = self.nodes[i]
        for subg in (self.subregions):
            # print(list(subg.G),n1,n2)
            # print(n1 in subg.G and n2 in subg.G)
            if n1 in subg.G:
                pp = subg.marginal(n1)
                break
        return pp

class subregion: 
    def __init__(self,G,boundaries,etype,epar,init,d,eps):
        self.G = G
        self.n = len(G)
        self.l = epar[0]
        if len(etype)>2:
            self.r = epar[1]
        self.d = d
        self.eps = eps
        self.getnid()

        self.boundaries = boundaries
        # print(list(G),boundaries)
        self.get_boundary_neigh()
        # print(list(G),init)
        t = init[0]
        for node in range(1,self.n):
            t = np.outer(t,init[node]).reshape(-1)
        self.T = t.reshape([self.d for _ in range(self.n)])
        self.get_operators(etype)
        # print(self.boundary_operator)

    def getnid(self):
        self.nid = {}
        nodes = list(self.G)
        for i in range(self.n):
            self.nid[nodes[i]] = i

    def get_boundary_neigh(self):
        neighs = []
        # print(list(self.G))
        for boundary in self.boundaries:
            if boundary != None: 
                neigh = set()
                for node in boundary:
                    neigh.update(list(self.G[node]))
                neigh = neigh.difference(set(boundary)) # 去掉边界本身，避免重复
                neighs.append(list(neigh))
            else:
                neighs.append(None)
        self.neighs_of_boundaries = neighs

    def get_operators(self,etype): #后面写成左乘了，所以算符的后指标是初态
        infc = np.eye(self.d**2).reshape(self.d,self.d,self.d,self.d)
        infc[1,1,0,1] += self.l
        infc[0,1,0,1] -= self.l
        infc[1,1,1,0] += self.l
        infc[1,0,1,0] -= self.l
        self.infc = infc.reshape(self.d*self.d,self.d*self.d)
        # print(self.infc)
        getinfc = np.zeros([self.d,self.d])
        getinfc[1,0] += self.l
        getinfc[0,0] -= self.l
        self.getinfc = getinfc

        local = np.eye(self.d)
        if len(etype)>2:
            local[2,1] += self.r
            local[1,1] -= self.r

        self.local = local

        self.get_boundary_operator()

        # print(local)
        
    def get_boundary_operator(self): # 相当于先给出约化的时间演化算符，只需要把条件概率缩并上去即可
        # print(list(self.G))
        self.boundary_operator = []
        for i in range(len(self.boundaries)):
            boundary = self.boundaries[i]
            if boundary != None:
                lb = len(boundary)
                neighs = self.neighs_of_boundaries[i]
                ln = len(neighs)
                identity = np.eye(self.d**(ln+lb)).reshape([self.d for _ in range(2*(ln+lb))])
                # identity2 = np.eye(self.d**(ln+lb-2)).reshape([self.d for _ in range(2*(ln+lb-2))])
                o = identity[None,None,:] # 扩张的两个维度是公用的
                for j in range(ln):
                    neigh = neighs[j]
                    o = np.swapaxes(o,lb+j+2,1)
                    neigh_in_boundary = set(self.G[neigh]).intersection(set(boundary))
                    for node in neigh_in_boundary:
                        idn = boundary.index(node)
                        o = np.swapaxes(o,idn+2,0)
                        # id_temp = identity2.reshape(o[0,0].shape)
                        o = np.tensordot(self.infc.reshape([self.d for _ in range(4)]),o,axes=((-2,-1),(0,1)))
                        o = np.swapaxes(o,idn+2,0)
                    o = np.swapaxes(o,lb+j+2,1)

                for j in range(lb):
                    n1 = boundary[j]
                    o = np.swapaxes(o,0,j+2)
                    for k in range(j+1,lb):
                        n2 = boundary[k]
                        if nx.has_path(self.G,n1,n2):
                            o = np.swapaxes(o,1,k+2)
                            o = np.tensordot(self.infc.reshape([self.d for _ in range(4)]),o,axes=((-2,-1),(0,1)))
                            o = np.swapaxes(o,1,k+2)
                    o = np.swapaxes(o,0,j+2)
                    
                o = np.squeeze(o) - identity
                o = np.sum(o.reshape([self.d**lb,self.d**ln,self.d**lb,self.d**ln]),axis=1)
                # print(boundary,neighs,o.reshape(self.d**lb,self.d**(lb+ln)))
                self.boundary_operator.append(o)
            else:
                self.boundary_operator.append(None)

    def o_out(self): # 此处把除以marginal得到条件概率和缩并约化时间演化算符得到相应marginal(也就是另一subregion的相应区域)的时间演化算符
        o_out = []
        # print(list(self.G))
        for i in range(len(self.boundaries)):
            boundary = self.boundaries[i]
            if boundary!= None:
                lb = len(boundary)
                neigh = self.neighs_of_boundaries[i]
                ln = len(neigh)
                # print(self.T)
                t = self.T

                # 把boundary和neigh放到最前,其他求和
                for _ in range(lb+ln):
                    t = t[None,:]
                for j in range(lb):
                    t = np.swapaxes(t,j,lb+ln+self.nid[boundary[j]])
                    # print(t.shape)
                for j in range(ln):
                    t = np.swapaxes(t,j+lb,lb+ln+self.nid[neigh[j]])
                    # print(t.shape)

                t = np.sum(t.reshape([self.d**lb,self.d**ln,-1]),axis = -1)
                marginal = np.sum(t,axis = -1)
                # print(list(self.G),boundary,neigh)
                # print(t,self.boundary_operator[i])
                w = np.einsum('ai,bai,a->ba',t,self.boundary_operator[i],safe_inv(marginal))
                # print(w)
                o_out.append(w + np.eye(self.d**lb))
                # print(o_out[-1])
            else:
                o_out.append(None)                                                            
        return o_out

    def update(self,msgin,o_in):
        # print(list(self.G))

        t = self.T
        for edge in list(self.G.edges()): #内部的感染
            [a,b] = edge
            i = self.nid[a]
            j = self.nid[b]
            if j<i:
                [i,j] = [j,i]
            t = np.swapaxes(np.swapaxes(t,i,0),j,1)
            t = t.reshape(self.d*self.d,-1)
            t = self.infc @ t
            t = t.reshape([self.d for _ in range(self.n)])
            t = np.swapaxes(np.swapaxes(t,j,1),i,0)
        # print(t)

        for i in range(len(self.boundaries)): # 相邻区域的感染
            boundary = self.boundaries[i]
            if boundary != None:
                l = len(boundary)
                o = o_in[i]
                for _ in range(l):
                    t = t[None,:]
                for j in range(l):
                    # print(j,l+self.nid[boundary[j]]-1)
                    t = np.swapaxes(t,j,l+self.nid[boundary[j]])
                    # print(t.shape)
                shape = list(t.shape)
                # print(shape,l)
                t = t.reshape([-1]+shape[l:])
                # print(boundary,o)
                # print(t.shape)
                # print(list(self.G),boundary,o.shape,t.shape)
                t = np.tensordot(o,t,axes=([-1],[0]))
                t = t.reshape(shape)
                for j in range(l):
                    t = np.swapaxes(t,j,l+self.nid[boundary[j]])
                t = t.reshape([self.d for _ in range(self.n)])

        # print(t)
        for i in range(self.n): # 外部的感染和各点的康复/恢复易染
            t = np.swapaxes(t,i,0)
            t = t.reshape(self.d,-1)
            t = self.local @ t
            if abs(msgin[i])>self.eps:
                t = (np.eye(self.d)+msgin[i]*self.getinfc) @ t
            t = t.reshape([self.d for _ in range(self.n)])
            t = np.swapaxes(t,i,0)
        # print(t)
        self.T = t

    def marginal(self,n1):
        i = self.nid[n1]
        marginal = np.sum(self.T,axis = tuple([dim for dim in range(self.n) if dim != i]))
        return marginal


# if __name__ == '__main__':
#     G,gname= graph('rrg',[20,3,1])
#     # G,gname = graph('qubics',[2])
#     # elist = [(0,1),(0,2),(0,3),(1,2),(2,3),(1,3)]
#     # G,gname = graph('elist',['test',elist])
#     t = time.time()
#     regions = get_Regions(G,6,6)
#     print(len(regions[0][0].edges()))
#     # for rg in regions:
#         # for part in rg:
#             # print(list(part),len(part))
#             # print(part.edges())
#         # print()
#     # print(len(regions))