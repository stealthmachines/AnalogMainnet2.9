#!/usr/bin/env python3
"""
HDGL Analog Mainnet Security & Performance Test Suite
Automated testing for the issues identified in the security audit
"""

import time
import requests
import threading
import concurrent.futures
import subprocess
import psutil
import json
from decimal import Decimal
import statistics

class SecurityPerformanceTests:
    def __init__(self):
        self.bridge_url = "http://localhost:9999"
        self.web_url = "http://localhost:8080"
        self.results = {}

    def test_api_rate_limiting(self):
        """Test if API endpoints are vulnerable to rate limiting attacks"""
        print("🔍 Testing API Rate Limiting...")

        start_time = time.time()
        responses = []

        # Send 100 rapid requests
        def make_request():
            try:
                resp = requests.get(f"{self.bridge_url}/api/status", timeout=1)
                return resp.status_code
            except:
                return 0

        with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
            futures = [executor.submit(make_request) for _ in range(100)]
            responses = [f.result() for f in futures]

        elapsed = time.time() - start_time
        success_rate = sum(1 for r in responses if r == 200) / len(responses)

        result = {
            "test": "API Rate Limiting",
            "requests": 100,
            "time_elapsed": elapsed,
            "success_rate": success_rate,
            "requests_per_second": 100 / elapsed,
            "vulnerability": success_rate > 0.9 and (100/elapsed) > 50  # Vulnerable if no rate limiting
        }

        print(f"   Requests/sec: {result['requests_per_second']:.1f}")
        print(f"   Success rate: {result['success_rate']:.2%}")
        print(f"   Vulnerable: {'⚠️  YES' if result['vulnerability'] else '✅ NO'}")

        self.results["rate_limiting"] = result

    def test_memory_usage_pattern(self):
        """Test memory usage patterns and potential leaks"""
        print("\n🔍 Testing Memory Usage Patterns...")

        # Get initial memory
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        memory_samples = []

        # Make 1000 requests to trigger potential memory leaks
        for i in range(1000):
            try:
                requests.get(f"{self.bridge_url}/api/status", timeout=0.5)
                if i % 100 == 0:
                    current_memory = process.memory_info().rss / 1024 / 1024
                    memory_samples.append(current_memory)
                    print(f"   Progress: {i}/1000, Memory: {current_memory:.1f}MB")
            except:
                pass

        final_memory = process.memory_info().rss / 1024 / 1024
        memory_growth = final_memory - initial_memory

        result = {
            "test": "Memory Usage Pattern",
            "initial_memory_mb": initial_memory,
            "final_memory_mb": final_memory,
            "memory_growth_mb": memory_growth,
            "memory_samples": memory_samples,
            "potential_leak": memory_growth > 10  # Flag if >10MB growth
        }

        print(f"   Initial: {initial_memory:.1f}MB")
        print(f"   Final: {final_memory:.1f}MB")
        print(f"   Growth: {memory_growth:.1f}MB")
        print(f"   Potential leak: {'⚠️  YES' if result['potential_leak'] else '✅ NO'}")

        self.results["memory_usage"] = result

    def test_consensus_performance(self):
        """Test consensus detection performance"""
        print("\n🔍 Testing Consensus Performance...")

        # Get multiple status samples to measure consensus timing
        response_times = []
        phase_variances = []

        for i in range(50):
            start = time.perf_counter()
            try:
                resp = requests.get(f"{self.bridge_url}/api/status", timeout=2)
                elapsed = time.perf_counter() - start
                response_times.append(elapsed * 1000)  # Convert to ms

                if resp.status_code == 200:
                    data = resp.json()
                    if 'phase_variance' in data:
                        phase_variances.append(float(data['phase_variance']))

            except Exception as e:
                print(f"   Request {i} failed: {e}")
                continue

        if response_times:
            avg_response_time = statistics.mean(response_times)
            p95_response_time = statistics.quantiles(response_times, n=20)[18]  # 95th percentile

            result = {
                "test": "Consensus Performance",
                "sample_count": len(response_times),
                "avg_response_time_ms": avg_response_time,
                "p95_response_time_ms": p95_response_time,
                "phase_variance_samples": phase_variances,
                "performance_grade": "A" if avg_response_time < 50 else "B" if avg_response_time < 100 else "C"
            }

            print(f"   Samples: {len(response_times)}")
            print(f"   Avg response: {avg_response_time:.2f}ms")
            print(f"   95th percentile: {p95_response_time:.2f}ms")
            print(f"   Performance: {result['performance_grade']}")

            self.results["consensus_performance"] = result

    def test_input_validation(self):
        """Test input validation on API endpoints"""
        print("\n🔍 Testing Input Validation...")

        # Test malicious payloads
        malicious_payloads = [
            {"test": "buffer_overflow", "data": "A" * 10000},
            {"test": "sql_injection", "data": "'; DROP TABLE users; --"},
            {"test": "xss_attempt", "data": "<script>alert('xss')</script>"},
            {"test": "path_traversal", "data": "../../../etc/passwd"},
            {"test": "null_bytes", "data": "test\x00.txt"},
            {"test": "unicode_overflow", "data": "\uFFFF" * 1000}
        ]

        vulnerabilities = []

        for payload in malicious_payloads:
            try:
                # Test POST to evolution endpoint if it exists
                resp = requests.post(f"{self.bridge_url}/api/evolution",
                                   json=payload, timeout=2)

                if resp.status_code == 200:
                    vulnerabilities.append(payload["test"])
                    print(f"   ⚠️  Vulnerable to: {payload['test']}")
                else:
                    print(f"   ✅ Protected from: {payload['test']}")

            except requests.exceptions.RequestException:
                print(f"   ✅ Rejected: {payload['test']}")

        result = {
            "test": "Input Validation",
            "payloads_tested": len(malicious_payloads),
            "vulnerabilities_found": vulnerabilities,
            "security_grade": "A" if len(vulnerabilities) == 0 else "C" if len(vulnerabilities) > 2 else "B"
        }

        print(f"   Vulnerabilities: {len(vulnerabilities)}/{len(malicious_payloads)}")
        print(f"   Security grade: {result['security_grade']}")

        self.results["input_validation"] = result

    def test_system_resource_usage(self):
        """Test system resource usage under load"""
        print("\n🔍 Testing System Resource Usage...")

        # Monitor system resources during sustained load
        cpu_samples = []
        memory_samples = []

        def monitor_resources():
            for _ in range(30):  # Monitor for 30 seconds
                cpu_percent = psutil.cpu_percent(interval=1)
                memory_percent = psutil.virtual_memory().percent
                cpu_samples.append(cpu_percent)
                memory_samples.append(memory_percent)

        def generate_load():
            # Generate sustained load
            for _ in range(300):
                try:
                    requests.get(f"{self.bridge_url}/api/status", timeout=0.5)
                    time.sleep(0.1)
                except:
                    pass

        # Run monitoring and load generation concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            monitor_future = executor.submit(monitor_resources)
            load_future = executor.submit(generate_load)

            # Wait for both to complete
            monitor_future.result()
            load_future.result()

        if cpu_samples and memory_samples:
            result = {
                "test": "System Resource Usage",
                "avg_cpu_percent": statistics.mean(cpu_samples),
                "max_cpu_percent": max(cpu_samples),
                "avg_memory_percent": statistics.mean(memory_samples),
                "max_memory_percent": max(memory_samples),
                "cpu_stability": statistics.stdev(cpu_samples) < 10,  # Low variance = stable
                "resource_grade": "A"
            }

            # Grade based on resource usage
            if result["max_cpu_percent"] > 80 or result["max_memory_percent"] > 80:
                result["resource_grade"] = "C"
            elif result["max_cpu_percent"] > 60 or result["max_memory_percent"] > 60:
                result["resource_grade"] = "B"

            print(f"   Avg CPU: {result['avg_cpu_percent']:.1f}%")
            print(f"   Max CPU: {result['max_cpu_percent']:.1f}%")
            print(f"   Avg Memory: {result['avg_memory_percent']:.1f}%")
            print(f"   Resource grade: {result['resource_grade']}")

            self.results["resource_usage"] = result

    def run_all_tests(self):
        """Run all security and performance tests"""
        print("🔒 HDGL Analog Mainnet Security & Performance Test Suite")
        print("=" * 60)

        try:
            # Verify services are running
            resp = requests.get(f"{self.bridge_url}/api/status", timeout=5)
            if resp.status_code != 200:
                print("❌ Bridge service not responding. Please start services first.")
                return
        except:
            print("❌ Cannot connect to bridge service. Please start services first.")
            return

        print("✅ Services detected, starting tests...\n")

        # Run all tests
        test_methods = [
            self.test_api_rate_limiting,
            self.test_memory_usage_pattern,
            self.test_consensus_performance,
            self.test_input_validation,
            self.test_system_resource_usage
        ]

        for test_method in test_methods:
            try:
                test_method()
            except Exception as e:
                print(f"❌ Test failed: {e}")

        # Generate summary report
        self.generate_summary_report()

    def generate_summary_report(self):
        """Generate final summary report"""
        print("\n" + "=" * 60)
        print("📊 SECURITY & PERFORMANCE SUMMARY")
        print("=" * 60)

        # Calculate overall grades
        security_issues = 0
        performance_issues = 0

        for test_name, result in self.results.items():
            if "vulnerability" in result and result["vulnerability"]:
                security_issues += 1
            if "potential_leak" in result and result["potential_leak"]:
                security_issues += 1

        # Overall security grade
        if security_issues == 0:
            security_grade = "A"
        elif security_issues <= 2:
            security_grade = "B"
        else:
            security_grade = "C"

        # Overall performance grade (based on response times)
        if "consensus_performance" in self.results:
            perf_grade = self.results["consensus_performance"]["performance_grade"]
        else:
            perf_grade = "Unknown"

        print(f"🔒 Overall Security Grade: {security_grade}")
        print(f"⚡ Overall Performance Grade: {perf_grade}")
        print(f"⚠️  Security Issues Found: {security_issues}")

        # Save detailed results
        with open("security_performance_results.json", "w") as f:
            json.dump(self.results, f, indent=2, default=str)

        print(f"\n📄 Detailed results saved to: security_performance_results.json")

        # Recommendations
        print("\n🎯 IMMEDIATE RECOMMENDATIONS:")
        if security_issues > 0:
            print("   1. Address security vulnerabilities found")
            print("   2. Implement rate limiting on API endpoints")
            print("   3. Add input validation and sanitization")
        if "memory_usage" in self.results and self.results["memory_usage"]["potential_leak"]:
            print("   4. Investigate memory leak in request handling")
        if "consensus_performance" in self.results:
            avg_time = self.results["consensus_performance"]["avg_response_time_ms"]
            if avg_time > 100:
                print("   5. Optimize consensus detection performance")

        print("\n✅ Audit completed successfully!")

if __name__ == "__main__":
    tester = SecurityPerformanceTests()
    tester.run_all_tests()