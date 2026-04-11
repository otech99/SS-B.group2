# SS-B.group2
Progetto di software security and blockchain : oracolo delle reti bayesiane
# git pull (da fare sempre prima del resto) per aggiornare le modifiche già fatte da altri
# "git add ." per tutto o "git add nome_file" 
# git commit -m "messaggio"
# git push

Pipx install eth-brownie (per configurare il framework brownie) 

Per installare e usare solhint (per analizzare la sicurezza dei contratti):
Installation
You can install Solhint using npm:

npm install -g solhint

verify that it was installed correctly:
solhint --version

Usage
First initialize a configuration file, if you don’t have one:

solhint --init
This will create a .solhint.json file with the recommended rules enabled. Then run Solhint with one or more Globs as arguments. For example, to lint all files inside contracts directory, you can do:

solhint 'contracts/**/*.sol'
To lint a single file:

solhint contracts/MyToken.sol
Run solhint without arguments to get more information:

Usage: solhint [options] <file> [...other_files]

Linter for Solidity programming language

Options:

  -V, --version                           output the version number
  -f, --formatter [name]                  report formatter name (stylish, table, tap, unix, json, compact, sarif)
  -w, --max-warnings [maxWarningsNumber]  number of allowed warnings, works in quiet mode as well
  -c, --config [file_name]                file to use as your rules configuration file (not compatible with multiple configs)
  -q, --quiet                             report errors only - default: false
  --ignore-path [file_name]               file to use as your .solhintignore
  --fix                                   automatically fix problems and show report
  --cache                                 only lint files that changed since last run
  --cache-location                        path to the cache file
  --noPrompt                              do not suggest to backup files when any `fix` option is selected
  --init                                  create configuration file for solhint
  --disc                                  do not check for solhint updates
  --save                                  save report to file on current folder
  --noPoster                              remove discord poster
  -h, --help                              output usage information

Commands:

  stdin [options]                         linting of source code data provided to STDIN
  list-rules                              display covered rules of current .solhint.json