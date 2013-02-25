(register-module [[name: shen-py]
                  [depends: py-kl]
                  [author: "Ramil Farkshatov"]
                  [license: "Shen license"]
                  [desc: "Shen-py"]
                  [load: "py-dump.shen"]
                  [dump-fn: py-dump-shen]])

(define py-dump-files
  {A --> (list string)}
  _ -> ["core.kl"
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

(define py-dump-shen
  {symbol --> symbol --> string --> string --> boolean}
  python _ Sdir Ddir -> (do (py-dump Sdir "shen-py.shen" Ddir)
                            (shenpy-mk-primitives Ddir)
                            (shenpy-call-with-install-flags
                             (freeze (map (/. X (py-dump Sdir X Ddir))
                                          (py-dump-files _))))
                          true))
