MKSHELL = rc
name = shen.py
python = python2

runtime_dir = runtime
shen_dir = shenpy

state_src = state.py

rt_src = \
  runtime.py

runtime_src = $rt_src $shen_dir/primitives.py

shen_src = \
  $shen_dir/primitives.py \
  $shen_dir/backend-utils.shen.py \
  $shen_dir/reg-kl.shen.py \
  $shen_dir/deinline-expr.shen.py \
  $shen_dir/klvm-trans.shen.py \
  $shen_dir/py-kl.shen.py \
  $shen_dir/primitives.shen.py \
  $shen_dir/shen-py.shen.py \
  $shen_dir/core.kl.py \
  $shen_dir/sys.kl.py \
  $shen_dir/sequent.kl.py \
  $shen_dir/yacc.kl.py \
  $shen_dir/writer.kl.py \
  $shen_dir/reader.kl.py \
  $shen_dir/prolog.kl.py \
  $shen_dir/track.kl.py \
  $shen_dir/declarations.kl.py \
  $shen_dir/load.kl.py \
  $shen_dir/macros.kl.py \
  $shen_dir/types.kl.py \
  $shen_dir/t-star.kl.py \
  $shen_dir/toplevel.kl.py \
  $shen_dir/modulesys.shen.py

all:V: $name

$shen_dir/stamp:Q:
  rm -f $target
  mkdir -p $shen_dir
  shen_run_sbcl -ne ./make.shen $shen_dir
  touch $target

$name:Q: $shen_dir/stamp $rt_src 
  { 
    echo '"""'
    cat LICENSE
    echo '"""'
    cat $rt_src
    if (! test -f $state_src) {
      echo
      cat dump.py
    }
    for (f in $shen_src) {
      echo
      echo '## '$f
      echo 'print("## file '^$"f^'")'
      awk '
        /^import shen.*$/ {next}
        {print}
        ' <$f
    }
    if (test -f $state_src) {
      cat $state_src
      echo 'if __name__ == "__main__":'
      echo '    repl()'
    }
    if not echo 'finish_dump()'
  } >$target

bootstrap:VQ: $shen_dir/stamp $rt_src
  rm -f $name $state_src
  mk
  echo '** Running Shen and dumping state'
  $python -O -m shen
  rm -f $name
  mk
  echo '** Compiling Shen'
  $python -O -c 'import shen;exit()'
