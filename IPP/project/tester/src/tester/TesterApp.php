<?php

/**
 * An integration testing script for the SOL26 interpreter.
 *
 * IPP: You can implement the entire tool in this file if you wish, but it is recommended to split
 * the code into multiple files and modules as you see fit.
 *
 * Author: Ondřej Ondryáš <iondryas@fit.vut.cz>
 *
 * AI usage notice: The author used OpenAI Codex to create the implementation of this
 * module based on its Python counterpart.
 */

declare(strict_types=1);

namespace IPP\Tester;

use RuntimeException;
use IPP\Tester\Cli\CliArguments;
use IPP\Tester\Cli\CliParser;
use IPP\Tester\Model\TestReport;
use IPP\Tester\Model\TestCaseDefinition;
use IPP\Tester\Model\TestCaseType;
use IPP\Tester\Model\TestCaseReport;
use IPP\Tester\Model\CategoryReport;
use IPP\Tester\Model\UnexecutedReason;
use IPP\Tester\Model\TestResult;
use Monolog\Formatter\LineFormatter;
use Monolog\Handler\AbstractHandler;
use Monolog\Handler\StreamHandler;
use Monolog\Level;
use Monolog\Logger;
use Monolog\Processor\IntrospectionProcessor;
use Monolog\Processor\PsrLogMessageProcessor;

/**
 * Coordinates the tester workflow: parse CLI args, configure logging, and
 * produce the final JSON report.
 */
class TesterApp
{
    /**
     * Configures the default logger.
     *
     * Logging level defaults to warning and can be raised by `-v` flags.
     *
     * IPP: You do not have to use logging – but it is the recommended practice.
     * See this for more information: https://seldaek.github.io/monolog/
     */
    private static function createLogger(): Logger
    {
        $logger = new Logger('main');
        $handler = new StreamHandler('php://stderr', Level::Warning);
        $handler->setFormatter(
            new LineFormatter(
                "%datetime% %level_name% [%channel%][%extra.class%:%extra.line%] %message%\n",
                'Y-m-d H:i:s',
                true,
                true,
                true
            )
        );

        $logger->pushProcessor(new PsrLogMessageProcessor());
        $logger->pushProcessor(new IntrospectionProcessor(Level::Debug));
        $logger->pushHandler($handler);

        return $logger;
    }

    private readonly Logger $logger;
    private readonly CliArguments $arguments;

    /**
     * @param list<string> $argv
     */
    public function __construct(array $argv)
    {
        // Set up logging
        $this->logger = TesterApp::createLogger();
        // Parse and validate command-line arguments before running the tool.
        $this->arguments = CliParser::parseArguments($this->logger, argv: $argv);
        // Verbosity affects only the selected log level.
        $this->configureLoggerVerbosity();
    }

    /**
     * Configures the logger based on the `-v` count.
     * 0 => warning, 1 => info, >=2 => debug.
     */
    private function configureLoggerVerbosity(): void
    {
        $level = Level::Warning;
        $verbosity = $this->arguments->verbose;

        if ($verbosity >= 2) {
            $level = Level::Debug;
        } elseif ($verbosity === 1) {
            $level = Level::Info;
        }

        foreach ($this->logger->getHandlers() as $handler) {
            if ($handler instanceof AbstractHandler) {
                $handler->setLevel($level);
            }
        }
    }

    /**
     * Writes the serialized JSON report either to file or stdout.
     */
    private function writeResult(TestReport $resultReport): void
    {
        $resultJson = json_encode($resultReport, JSON_PRETTY_PRINT);

        if (!\is_string($resultJson)) {
            throw new RuntimeException('Failed to serialize report to JSON.');
        }

        $outputFile = $this->arguments->output;
        if ($outputFile !== null) {
            $written = file_put_contents($outputFile, $resultJson);

            if ($written === false) {
                throw new RuntimeException(
                    sprintf('Failed to write output file: %s', $outputFile)
                );
            }

            return;
        }
        else {
            fwrite(STDOUT, $resultJson . PHP_EOL); // Do terminálu
        }

        fwrite(STDOUT, $resultJson . PHP_EOL);
    }

    /**
     * Parses a single .test file and discovers associated files.
     * * @param string $filePath Path to the .test file.
     * @return TestCaseDefinition The parsed test case definition.
     * @throws RuntimeException If the file cannot be read.
     */
    private function parseTestFile(string $filePath): array
    {
        $content = file_get_contents($filePath);
        if ($content === false) {
            throw new RuntimeException("Failed to read file: $filePath");
        }

        // Rozdělíme soubor na HLAVIČKU a KÓD podle prvního výskytu "class " nebo "["
        // Protože metadata končí tam, kde začíná SOL26 kód.
        $lines = explode("\n", $content);
        $name = pathinfo($filePath, PATHINFO_FILENAME);
        $dir = dirname($filePath);

        $description = null;
        $category = 'default';
        $points = 1;
        $expectedC = [];
        $expectedI = [];
        $sourceCodeLines = [];
        $headerFinished = false;

        foreach ($lines as $line) {
            $lineR = rtrim($line);

            if (!$headerFinished) {
                // Detekce metadat
                if (str_starts_with($lineR, '***')) {
                    $description = trim(substr($lineR, 3));
                    continue;
                } elseif (str_starts_with($lineR, '+++')) {
                    $category = trim(substr($lineR, 3));
                    continue;
                } elseif (str_starts_with($lineR, '!C!')) {
                    $expectedC[] = (int)trim(substr($lineR, 3));
                    continue;
                } elseif (str_starts_with($lineR, '!I!')) {
                    $expectedI[] = (int)trim(substr($lineR, 3));
                    continue;
                } elseif (str_starts_with($lineR, '>>>')) {
                    $points = (int)trim(substr($lineR, 3));
                    continue;
                }

                // KLÍČOVÁ ZMĚNA: Pokud řádek není prázdný a nezačíná metadaty,
                // je to už kód a HLAVIČKA KONČÍ.
                if (trim($lineR) !== "") {
                    $headerFinished = true;
                    // Tento řádek už patří do kódu, takže ho nesmíme zahodit!
                } else {
                    continue; // Přeskoč prázdné řádky mezi metadaty a kódem
                }
            }

            $sourceCodeLines[] = $line;
        }


        $sourceCode = implode("\n", $sourceCodeLines);
        $type = (empty($expectedC) && !empty($expectedI)) ? TestCaseType::EXECUTE_ONLY : TestCaseType::COMBINED;
        if (!empty($expectedC) && empty($expectedI)) $type = TestCaseType::PARSE_ONLY;

        $definition = new TestCaseDefinition(
            $name, $filePath, $type, $category,
            file_exists("$dir/$name.in") ? "$dir/$name.in" : null,
            file_exists("$dir/$name.out") ? "$dir/$name.out" : null,
            $description, $points,
            !empty($expectedC) ? $expectedC : null,
            !empty($expectedI) ? $expectedI : null
        );

        return ['definition' => $definition, 'source' => $sourceCode];
    }

    /**
     * Discovers all .test files in the given directory.
     * * @param string $directory The directory to search in.
     * @param bool $recursive Whether to search recursively.
     * @return list<string> A list of paths to discovered .test files.
     */
    private function findTestFilePaths(string $directory, bool $recursive): array
    {
        $paths = [];
        $flags = \FilesystemIterator::SKIP_DOTS;
        $iterator = $recursive
            ? new \RecursiveIteratorIterator(new \RecursiveDirectoryIterator($directory, $flags))
            : new \DirectoryIterator($directory);

        foreach ($iterator as $file) {
            if ($file->isFile() && $file->getExtension() === 'test') {
                $paths[] = $file->getRealPath();
            }
        }
        return $paths;
    }

    /**
     * Executes the testing logic.
     *
     * @return int The process exit code.
     */
    public function run(): int
    {
        if (!is_dir($this->arguments->testsDir)) {
            return 1;
        }

        $paths = $this->findTestFilePaths($this->arguments->testsDir, $this->arguments->recursive);
        $discoveredTestCases = [];
        $unexecuted = [];

        $catResults = [];
        $catScores = [];
        $catTotals = [];

        foreach ($paths as $path) {
            $testName = pathinfo($path, PATHINFO_FILENAME);
            try {
                $parsed = $this->parseTestFile($path);
                $test = $parsed['definition'];
                $sourceCode = $parsed['source'];

                $discoveredTestCases[] = $test;

                if (!$this->shouldIncludeTest($test) || $this->arguments->dryRun) {
                    continue;
                }

                $cat = $test->category;
                if (!isset($catResults[$cat])) {
                    $catResults[$cat] = [];
                    $catScores[$cat] = 0;
                    $catTotals[$cat] = 0;
                }

                // Body do celkového součtu kategorie přičteme hned, jak test "přijmeme" k exekuci
                $catTotals[$cat] += $test->points;

                $testCaseReport = $this->executeTestCase($test, $sourceCode);
                $catResults[$cat][$test->name] = $testCaseReport;

                // Body do passed přičteme jen při úspěchu
                if ($testCaseReport->result === TestResult::PASSED) {
                    $catScores[$cat] += $test->points;
                }

            } catch (\Exception $e) {
                $unexecuted[$testName] = new UnexecutedReason($e->getMessage());
            }
        }

        $finalCategoryReports = [];
        foreach ($catResults as $catName => $tests) {
            // Prohodil jsem proměnné, aby total byl první
            $finalCategoryReports[$catName] = new CategoryReport(
                $catTotals[$catName], // 1. Total (v JSONu to chceš jako první)
                $catScores[$catName], // 2. Passed
                $tests
            );
        }

        $report = new TestReport($discoveredTestCases, $unexecuted, $finalCategoryReports);
        $this->writeResult($report);

        return 0;
    }

    /**
     * Runs an external command and captures its output.
     * * @param list<string> $cmd The command to execute.
     * @param string|null $stdinPath Path to the file for standard input.
     * @return array{code: int, stdout: string, stderr: string}
     * @throws RuntimeException If the command fails to start.
     */
    private function runCommand(array $cmd, ?string $stdinPath = null, ?array $env = null): array
    {
        $descriptors = [
            0 => $stdinPath ? ["file", $stdinPath, "r"] : ["pipe", "r"],
            1 => ["pipe", "w"],
            2 => ["pipe", "w"]
        ];

        $process = proc_open($cmd, $descriptors, $pipes, null, $env);
        if (!is_resource($process)) {
            throw new RuntimeException("Failed to execute command: " . implode(' ', $cmd));
        }

        if (!$stdinPath) {
            fclose($pipes[0]);
        }

        $stdout = stream_get_contents($pipes[1]);
        $stderr = stream_get_contents($pipes[2]);

        fclose($pipes[1]);
        fclose($pipes[2]);
        $exitCode = proc_close($process);

        return ['code' => $exitCode, 'stdout' => $stdout, 'stderr' => $stderr];
    }

    /**
     * Executes a single test case through translation and interpretation.
     *
     * @param TestCaseDefinition $test The test case definition to execute.
     * @param string $sourceCode Clean source code without test metadata.
     * @return TestCaseReport The result report for the test case.
     */
    private function executeTestCase(TestCaseDefinition $test, string $sourceCode): TestCaseReport
    {
        $parserExitCode = null; $parserStdout = null; $parserStderr = null;
        $interpreterExitCode = null; $interpreterStdout = null; $interpreterStderr = null;
        $diff = null;
        $tempFiles = [];

        // 1. Příprava čistého zdrojového kódu
        $srcTmp = tempnam(sys_get_temp_dir(), 'ipp_src_');
        file_put_contents($srcTmp, $sourceCode);
        $tempFiles[] = $srcTmp;
        $fileToRun = $srcTmp;

        // 2. Fáze překladu (SOL2XML / Parser)
        if ($test->testType !== TestCaseType::EXECUTE_ONLY) {
            $res = $this->runCommand(['python3', '/src/sol_to_xml.py', $srcTmp]);
            $parserExitCode = $res['code'];
            $parserStdout = $res['stdout'];
            $parserStderr = $res['stderr'];

            if ($parserExitCode === 0) {
                $xmlTmp = tempnam(sys_get_temp_dir(), 'ipp_xml_');
                file_put_contents($xmlTmp, $res['stdout']);
                $fileToRun = $xmlTmp;
                $tempFiles[] = $xmlTmp;
            }
        }

        // 3. Fáze interpretace
        // Spustí se pokud: je to EXECUTE_ONLY NEBO (je to COMBINED a parser uspěl)
        if ($test->testType === TestCaseType::EXECUTE_ONLY ||
            ($test->testType === TestCaseType::COMBINED && $parserExitCode === 0)) {

            // Upravíme příkaz tak, aby odpovídal tvé struktuře:
            // 1. Nastavíme PYTHONPATH (pro jistotu přímo v commandu)
            // 2. Spustíme solint.py místo interpret.py

            $cmd = [
                'python3',
                '/src/int/src/solint.py', // Upravená cesta k tvému souboru
                '--source',
                $fileToRun
            ];

            // Aby fungovaly importy uvnitř tvého interpretu, musíme nastavit environment
            // To uděláme tak, že do proc_open pošleme upravené env pole
            $env = array_merge($_ENV, ['PYTHONPATH' => '/src/int/src']);

            $res = $this->runCommand($cmd, $test->stdinFile, $env);
            $interpreterExitCode = $res['code'];
            $interpreterStdout = $res['stdout'];
            $interpreterStderr = $res['stderr'];
        }

        // 4. Validace výsledků
        $finalResult = TestResult::PASSED;
        $isCodeOk = false;

        if ($test->testType === TestCaseType::PARSE_ONLY) {
            // Validace pouze parseru
            $expectedCodes = $test->expectedParserExitCodes ?? [0];
            $isCodeOk = in_array($parserExitCode, $expectedCodes);
            if (!$isCodeOk) {
                $finalResult = TestResult::UNEXPECTED_PARSER_EXIT_CODE;
            }
        } else {
            // Validace pro COMBINED nebo EXECUTE_ONLY
            if ($test->testType === TestCaseType::COMBINED && $parserExitCode !== 0) {
                // Pokud u COMBINED selhal parser, je to chyba parseru (i kdyby interpret čekal nenulu)
                $isCodeOk = false;
                $finalResult = TestResult::UNEXPECTED_PARSER_EXIT_CODE;
            } else {
                // Validace interpretu
                $expectedCodes = $test->expectedInterpreterExitCodes ?? [0];
                // Pozor: null (interpret neběžel) nikdy neprojde in_array([0])
                $isCodeOk = ($interpreterExitCode !== null) && in_array($interpreterExitCode, $expectedCodes);
                if (!$isCodeOk) {
                    $finalResult = TestResult::UNEXPECTED_INTERPRETER_EXIT_CODE;
                }
            }
        }

        // 5. Kontrola výstupu (diff) - pouze pokud exit kódy sedí a jsou 0
        if ($isCodeOk && $finalResult === TestResult::PASSED) {
            $lastExitCode = ($test->testType === TestCaseType::PARSE_ONLY) ? $parserExitCode : $interpreterExitCode;

            if ($lastExitCode === 0 && $test->expectedStdoutFile) {
                $tmpOut = tempnam(sys_get_temp_dir(), 'ipp_out_');
                file_put_contents($tmpOut, $interpreterStdout ?? "");

                $diffRes = $this->runCommand(['diff', $tmpOut, $test->expectedStdoutFile]);
                if ($diffRes['code'] !== 0) {
                    $finalResult = TestResult::INTERPRETER_RESULT_DIFFERS;
                    $diff = $diffRes['stdout'];
                }
                $tempFiles[] = $tmpOut;
            }
        }

        // Úklid dočasných souborů
        foreach ($tempFiles as $f) {
            if (file_exists($f)) @unlink($f);
        }

        return new TestCaseReport(
            $finalResult,
            $parserExitCode,
            $interpreterExitCode,
            $parserStdout,
            $parserStderr,
            $interpreterStdout,
            $interpreterStderr,
            $diff
        );
    }

    /**
     * Determines whether a test case should be included based on CLI arguments.
     * * @param TestCaseDefinition $test The test case to check.
     * @return bool True if the test should be executed.
     */
    private function shouldIncludeTest(TestCaseDefinition $test): bool
    {
        $args = $this->arguments;
        $useRegex = $args->regexFilters;

        // Pomocná funkce pro kontrolu shody (string vs regex)
        $matches = function (string $subject, ?array $filters) use ($useRegex): bool {
            if ($filters === null) return false;
            foreach ($filters as $f) {
                if ($useRegex) {
                    // Použijeme @ jako oddělovač, aby se nekouslo s lomítky v cestách
                    if (preg_match('@' . $f . '@', $subject)) return true;
                } else {
                    if ($subject === $f) return true;
                }
            }
            return false;
        };

        // 1. Logika pro INCLUDE
        $hasInclude = ($args->include !== null || $args->includeTest !== null || $args->includeCategory !== null);
        $isIncluded = !$hasInclude; // Pokud není filtr, bereme vše

        if ($hasInclude) {
            if ($matches($test->name, $args->include) ||
                $matches($test->name, $args->includeTest) ||
                $matches($test->category, $args->include) ||
                $matches($test->category, $args->includeCategory)) {
                $isIncluded = true;
            }
        }

        // 2. Logika pro EXCLUDE (přebíjí vše)
        if ($matches($test->name, $args->exclude) ||
            $matches($test->name, $args->excludeTest) ||
            $matches($test->category, $args->exclude) ||
            $matches($test->category, $args->excludeCategory)) {
            return false;
        }

        return $isIncluded;
    }
}