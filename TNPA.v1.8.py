from TNPA_Epidemics_1 import *
import argparse

'''
本版本主要实现的内容：
包体现在具有独立的版本号了
为了保持一致性构建了新的subg划分方案

'''

def print_region(G,R,N):
    regions = get_Regions(G,R,N) 
    n = 0
    # print(len(regions))
    for region in regions:
        # print(len(region[0].edges()))
        n += len(list(region.graph))
        print(list(region.graph),list(region.graph.edges()))
        if region.subg:
            print('subregions:')
            for subg in region.subregions:
                # print(list(subg))
                print(list(subg),list(subg.edges()),len(subg))
            if region.intersec:
                print('intersections:')
                for intersec in region.intersections:
                    # print(list(intersec))
                    print(list(intersec),list(intersec.edges()),len(intersec))
        print()
    print(n)

def print_region_diction(G,R,N):
    regions_dict = get_Regions_diction(G,R,N) 
    # print(len(regions))
    for r in range(3,R+1):
        n = 0
        print('R='+str(r))
        for region in regions_dict[r]:
            n += len(list(region.graph))
            print(list(region.graph)) #,list(region.graph.edges())
            if region.subg:
                print('subregions:')
                for part in region.subregions:
                    print(list(part))
            print()
        print(n)

if __name__ == '__main__':

    eps = 1e-7
    precision = 5
    np.set_printoptions(precision=3,floatmode='maxprec',suppress=True)


    # print('Graph:')
    # gtype = input("graph_type: ")
    # if gtype in ['club','macrotree']:
    #     G,gname = graph(gtype)
    # else:
    #     gn = eval(input("graph_size: "))
    #     if gtype == 'qubic':
    #         num = gn//2-1
    #         G,gname = graph(gtype,[num])
    #     else:
    #         seed = eval(input("seed: "))
    #         if gtype == 'tree':
    #             G,gname = graph(gtype,[gn,seed])
    #         else:
    #             c = eval(input("average_degree: "))
    #             if gtype == 'smallworld':
    #                 p = eval(input("reconnect: "))
    #                 G,gname = graph(gtype,[gn,c,p,seed])
    #             else:
    #                 if gtype == 'erg':
    #                     G,gname = graph(gtype,[gn,c/gn,seed])
    #                 else:
    #                     G,gname = graph(gtype,[gn,c,seed])
    # clique = input('Add clique? y or n ')
    # if clique == 'y':
    #     n = eval(input('number of clique: '))
    #     stepped = input("stepped size or constant size? s or c ")
    #     if stepped == 'c':
    #         stepped = False
    #     elif stepped == 's':
    #         stepped = True
    #     size = eval(input(int(stepped) * 'max' + 'size of clique(>=3): '))
    #     G = add_clique(G,n,size,seed,stepped)
    #     gname = str(n) + '*' + int(stepped) * '(3,' + str(size) + stepped*')' + 'cliqued_' + gname
    
    # propose = input("target(r for region,e for evolution and epidemic): ")

    # if propose == 'r': # 测试Region_generator
    #     method = input("method(s for one group of set, m for multi): ")
    #     if method == 's':
    #         R = eval(input("R= "))
    #         N = eval(input("N= "))
    #         print_region(G,R,N)
    #     elif method == 'm':
    #         R = eval(input("R_max= "))
    #         for r in range(3,R+1):
    #             print_region(G,r,r)
    # elif propose == 'e':
    #     print("Evolution parameter")
    #     print("About time:")
    #     default = input("use default setting (200/0.1)?:y or n ")
    #     if default == 'y':
    #         t_max = 200
    #         tau = 0.1
    #     else:
    #         t_max = eval(input('t_max:'))
    #         tau = eval(input('tau:'))
    #     print("About Epidemic")
    #     default = input("use default setting (SIR:0.1,0.05)?:y or n ")
    #     if default == 'y':
    #         etype = 'SIR'
    #         l = 0.1
    #         r = 0.05
    #     else:
    #         etype = input("etype:")
    #         l = eval(input('lambda:'))
    #         r = eval(input('rho:'))
    #     epar = [l,r]
    #     init = None
    #     inits = []
    #     while init != '':
    #         init = input('init(press enter to continue): ')
    #         if init != '':
    #             inits.append(eval(init))
        
    #     print("About method")
    #     target = input("target(e for data and error up to MCMC, d for data only): ")
    #     if target == 'e':
    #         print('set MCMC:')
    #         default = input("use default setting (1000000,40)?:y or n ")
    #         if default == 'y':
    #             repeats = 1000000
    #             mp_num = 40
    #         elif default == 'n':
    #             repeats = eval(input('MCMC_repeats:'))
    #             mp_num = eval(input('MCMC_multiprocess_number:'))
    #     print("input methods("+(target == 'd')*"MCMC,"+"DMP,PA,TNPA), press enter to continue")
    #     method = None
    #     methods = []
    #     while True:
    #         method = input("method("+(target == 'd')*"MCMC,"+"DMP,PA,TNPA):")
    #         if method in methods:
    #             print("Repeated inputs. Try another one?")
    #         elif target == 'e' and method == 'MCMC':
    #             print("Obviously it's 0. What can I say? Try another one?")
    #         elif method in ['MCMC','DMP','PA','TNPA']:
    #             if method == 'TNPA':
    #                 RNs = []
    #                 while True:
    #                     print("print all R&N pairs you want:(press enter at any step to finish)")
    #                     r = input('R:')
    #                     if r != '':
    #                         n = input('N:')
    #                         if n != '':
    #                             RNs.append([eval(r),eval(n)])
    #                         else:
    #                             break
    #                     else:
    #                         break
    #             if method == 'MCMC':
    #                 repeats = input('repeats:')
    #                 mp_num = input('multiprocess_number:')
    #             methods.append(method)
    #         elif method == '':
    #             break
    #         else:
    #             print("Sorry, this method is unavailable now. Try another one?")

    #     if target == 'e' or 'MCMC' in methods:
    #         s_mc = Epidemic(G,gname,etype,epar,tau)
    #         s_mc.sys_init(inits)
    #         repeats = input('')
    #         s_mc.MCMC_init(repeats= repeats,mp_num=mp_num)
    #         s_mc.update_to(t_max)
    #         s_mc.save_data(precision)
    #     methods.remove('MCMC')
    #     simulations = []
    #     for method in methods:
    #         s = Epidemic(G,gname,etype,epar,tau)
    #         s.sys_init(inits)
    #         if method == 'TNPA':
    #             while len(RNs)>0:
    #                 rn = RNs.pop()
    #                 [r,n] = rn
    #                 s.TNPA_init(r,n)
    #                 if len(RNs)>0:
    #                     s.update_to(t_max)
    #                     s.save_data(precision)
    #                     simulations.append(s)
    #                     s = Epidemic(G,gname,etype,epar,tau)
    #                     s.sys_init(inits)
    #         else:
    #             if method == 'DMP':
    #                 s.DMP_init()
    #             elif method == 'PA':
    #                 s.PA_init()
    #         s.update_to(t_max)
    #         s.save_data(precision)

    #     if target == 'e':
    #         for s in simulations:
    #             s.save_error(s_mc.marginal_all,precision)

                
    # else:
    #     print('Wrong command')

    G = nx.random_tree(200,seed = 1)
    gname = 'random_tree_seed=1_n=200'

    n = 10
    k = 3
    seed = 1

    G = add_clique(G,n,k,seed)
    gname = str(n) + '*' + str(k) + 'cliqued_' + gname

    t_max = 200
    # tau = 1.
    tau = 0.1
    
    # # rho = 0.1
    rho = 0.05
    lamda = 0.1

    etype = 'SIR'
    epar = [lamda,rho]

    ini = [0]
    
    # elist = [(0,1),(0,2),(0,3),(4,1),(4,2),(5,1),(5,3),(6,2),(6,3)]
    # G,gname = graph('elist',['test',elist])

    # elist = [(0,1),(0,2),(1,3),(2,3),(4,2),(5,3),(5,4),(5,6),(6,0)]
    # G,gname = graph('elist',['test2',elist])

    # 模型参数

    if True:
        s_MC = Epidemic(G,gname,etype,epar,tau)
        s_MC.sys_init(ini)
        s_MC.MCMC_init(repeats= 1000000,mp_num=40)
        s_MC.update_to(t_max)
        s_MC.save_data(precision)

        s = Epidemic(G,gname,etype,epar,tau)
        s.sys_init(ini)
        s.PA_init()
        s.update_to(t_max)
        s.save_data(precision)
        s.save_error(s_MC.marginal_all,precision)

        s = Epidemic(G,gname,etype,epar,tau)
        s.sys_init(ini)
        s.DMP_init()
        s.update_to(t_max)
        s.save_data(precision)
        s.save_error(s_MC.marginal_all,precision)

        R = 9
        N = 9
        region_dict = get_Regions_diction(G,R,N)
        for r in range(3,R+1):
            label = '_R=' + str(r)  + '_N=' + str(N)
            s = Epidemic(G,gname,etype,epar,tau)
            s.sys_init(ini)
            s.TNPA_init(region_dict[r],label)
            s.update_to(t_max)
            s.save_data(precision)
            s.save_error(s_MC.marginal_all,precision)
        
    else:
        print_region_diction(G,9,9)

# nohup python -u TNPA.v1.3.py >/dev/null 2>&1 &