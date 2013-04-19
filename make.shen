#!/usr/bin/env shen_run

(define main
  _ -> (do (use-modules [shen-py])
					 (set py.*same-namespace* true)
					 (set py.*in-repl* false)
           (dump-module shen-py python all "shenpy/")
					 true))
