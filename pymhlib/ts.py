
from pymhlib.scheduler import Method, Scheduler
from pymhlib.solution import Solution
from pymhlib.demos.maxsat import MAXSATInstance, MAXSATSolution
from pymhlib.ts_helper import TabuList

from typing import List, Callable, Any
import time
import random as rd



class TS(Scheduler):

    def __init__(self, sol: Solution, meths_ch: List[Method], meths_rli: List[Method],
                min_ll: int=5, max_ll: int=5, change_ll_iter: int=1,
                own_settings: dict = None, consider_initial_sol=False):
        super().__init__(sol, meths_ch+meths_rli, own_settings, consider_initial_sol)

        self.tabu_list = TabuList(min_ll, max_ll, change_ll_iter)
        self.meths_ch = meths_ch
        self.meths_rli = meths_rli 

    def update_tabu_list(self, sol: Solution, sol_old: Solution):
        self.tabu_list.update_list()
        l = self.tabu_list.generate_list_length(self.iteration)
        self.tabu_list.append(sol.get_tabu_attribute(sol_old), l)
    
    
    def ts(self, sol: Solution):

        while True:
            for m in self.next_method(self.meths_rli, repeat=True):
                sol_old = sol.copy()

                def ts_iteration(sol: Solution, _par, result):
                    m.func(sol, m.par, best_improvement=True, tabu_list=self.tabu_list, incumbent=self.incumbent)
                ts_method = Method(m.name, ts_iteration, self.tabu_list.generate_list_length(self.iteration))

                #if self.step_logger.hasHandlers():
                 #   self.step_logger.info()

                t_start = time.process_time()
                res = self.perform_method(ts_method, sol, delayed_success=True)
                self.update_tabu_list(sol, sol_old)
                self.delayed_success_update(m, sol.obj(), t_start, sol_old)
                if res.terminate:
                    return


    def run(self) -> None:
        sol = self.incumbent.copy()
        assert self.incumbent_valid or self.meths_ch
        self.perform_sequentially(sol, self.meths_ch)
        self.ts(sol)









if __name__ == '__main__':
    from pymhlib.settings import get_settings_parser, settings
    parser = get_settings_parser()
    settings.mh_titer=50
    settings.mh_out='summary.log'
    def meth_rli(sol: MAXSATSolution, par, res):
        sol.x[0] = not sol.x[0]
        print('   restricted local search with tabulist', par)

    def get_tabu_attribute(sol, old_sol):
        print('   calculate changed elem an return it', sol, old_sol)
        elem = -1
        for i, e in enumerate(sol.x):
            if bool(e) != bool(old_sol.x[i]):
                elem = i+1 if e else -(i+1)
                print('       elem', elem)
                return elem
        return None
        
    m_rli = Method('rli1',meth_rli,None)

    inst = MAXSATInstance('maxsat-simple.cnf')
    sol = MAXSATSolution(inst)
    ts = TS(sol,[Method('ch',MAXSATSolution.construct,0)], [m_rli], get_tabu_attribute)
    ts.run()