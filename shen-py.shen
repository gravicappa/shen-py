(defun eval-kl [X]
  (let X (py-from-kl [(kl-from-shen X)])
    (shenpy-eval X)))
