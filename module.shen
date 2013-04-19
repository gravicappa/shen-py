(register-module [[name: shen-py]
                  [depends: py-kl]
                  [author: "Ramil Farkshatov"]
                  [license: "Shen license"]
                  [desc: "Shen-py"]
                  [dump-fn: py.dump-shen]])

(define py.dump-files
  {--> (list string)}
  -> ["core.kl"
      "declarations.kl"
      "load.kl"
      "macros.kl"
      "prolog.kl"
      "reader.kl"
      "sequent.kl"
      "sys.kl"
      "toplevel.kl"
      "track.kl"
      "t-star.kl"
      "types.kl"
      "writer.kl"
      "yacc.kl"])

(define py.dump-shen
  {symbol --> symbol --> string --> string --> boolean}
  python _ Sdir Ddir -> (do (backend-utils.write-file
                             (py.generate-primitives)
                             (cn Ddir "/primitives.py"))
                            (py.dump Sdir "shen-py.shen" Ddir)
                            (map (/. X (py.dump Sdir X Ddir))
                                 (py.dump-files))
                            true))
