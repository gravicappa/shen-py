(defun eval-kl (X)
  (trap-error (let . (set py.*same-namespace* true)
                (let R (shenpy.eval (py-from-kl (cons (kl-from-shen X) ())))
                  (let . (set py.*same-namespace* false)
                    R)))
              (lambda E (do (set py.*same-namespace* false)
                            (error (error-to-string E))))))
