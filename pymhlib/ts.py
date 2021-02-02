
from pymhlib.scheduler import Method, Scheduler
from pymhlib.solution import Solution
from pymhlib.demos.maxsat import MAXSATInstance, MAXSATSolution
from pymhlib.ts_helper import TabuList

from typing import List, Callable, Any
import time
import random as rd
import logging



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
        if self.incumbent_iteration == self.iteration and self.incumbent.is_tabu(self.tabu_list):
            # a new incumbent was found, but it was tabu (aspiration criterion)
            # get the violated tabu attribute and delete it from the list
            tabu_attribute = sol_old.get_tabu_attribute(self.incumbent)
            self.tabu_list.delete_attribute(tabu_attribute)
            if self.step_logger.hasHandlers():
                self.step_logger.info(f'TA_DEL: {tabu_attribute}')
        else:
            l = self.tabu_list.generate_list_length(self.iteration)
            self.tabu_list.add_attribute(sol.get_tabu_attribute(sol_old), l)

    
    
    def ts(self, sol: Solution):

        
        while True:
            # use of multiple different methods for restricted neighborhood search is possible,
            # but usually only one is used
            for m in self.next_method(self.meths_rli, repeat=True):
                sol_old = sol.copy()
                def ts_iteration(sol: Solution, _par, result):
                    m.func(sol, m.par, best_improvement=True, tabu_list=self.tabu_list, incumbent=self.incumbent)
                ts_method = Method(m.name, ts_iteration, self.tabu_list.generate_list_length(self.iteration))

                t_start = time.process_time()
                res = self.perform_method(ts_method, sol, delayed_success=True)
                self.update_tabu_list(sol, sol_old)
                self.delayed_success_update(m, sol.obj(), t_start, sol_old)

                if self.step_logger.hasHandlers():
                    self.step_logger.info(f'LL: {self.tabu_list.current_ll}')
                    for ta in self.tabu_list.tabu_list:
                        self.step_logger.info(f'TA: {ta}')

                if res.terminate:
                    return


    def run(self) -> None:
        sol = self.incumbent.copy()
        assert self.incumbent_valid or self.meths_ch
        self.perform_sequentially(sol, self.meths_ch)
        self.ts(sol)





