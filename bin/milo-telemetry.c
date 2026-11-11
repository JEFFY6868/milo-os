#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/statvfs.h>
#include <unistd.h>
#include <time.h>

int main(void) {
    // 1. Memory from /proc/meminfo
    FILE *f = fopen("/proc/meminfo", "r");
    long total_kb = 0, avail_kb = 0;
    if (f) {
        char line[128];
        while (fgets(line, sizeof(line), f)) {
            if (strncmp(line, "MemTotal:", 9) == 0) sscanf(line + 9, "%ld", &total_kb);
            else if (strncmp(line, "MemAvailable:", 13) == 0) sscanf(line + 13, "%ld", &avail_kb);
        }
        fclose(f);
    }
    long used_kb = total_kb - avail_kb;
    int mem_pct = total_kb > 0 ? (int)((used_kb * 100) / total_kb) : 0;
    double used_gb = (double)used_kb / (1024.0 * 1024.0);
    double total_gb = (double)total_kb / (1024.0 * 1024.0);

    // 2. Disk from statvfs
    struct statvfs st;
    double disk_free_gb = 0.0;
    int disk_pct = 0;
    if (statvfs("/", &st) == 0) {
        double d_total = (double)(st.f_blocks * st.f_frsize) / (1024.0 * 1024.0 * 1024.0);
        disk_free_gb = (double)(st.f_bavail * st.f_frsize) / (1024.0 * 1024.0 * 1024.0);
        disk_pct = d_total > 0 ? (int)(((d_total - disk_free_gb) * 100) / d_total) : 0;
    }

    // 3. CPU calculation from /proc/stat with delta
    long user, nice, system, idle, iowait, irq, softirq, steal;
    int cpu_pct = 5;
    f = fopen("/proc/stat", "r");
    if (f) {
        if (fscanf(f, "cpu %ld %ld %ld %ld %ld %ld %ld %ld",
                   &user, &nice, &system, &idle, &iowait, &irq, &softirq, &steal) == 8) {
            long total = user + nice + system + idle + iowait + irq + softirq + steal;
            long idle_all = idle + iowait;

            FILE *cf = fopen("/tmp/milo-cpu.stat", "r");
            long prev_total = 0, prev_idle = 0;
            if (cf) {
                if (fscanf(cf, "%ld %ld", &prev_total, &prev_idle) == 2) {
                    long d_total = total - prev_total;
                    long d_idle = idle_all - prev_idle;
                    if (d_total > 0) {
                        cpu_pct = (int)(((d_total - d_idle) * 100) / d_total);
                    }
                }
                fclose(cf);
            }
            cf = fopen("/tmp/milo-cpu.stat", "w");
            if (cf) {
                fprintf(cf, "%ld %ld\n", total, idle_all);
                fclose(cf);
            }
        }
        fclose(f);
    }
    if (cpu_pct < 1) cpu_pct = 1;
    if (cpu_pct > 99) cpu_pct = 99;

    // 4. Core Temp
    int temp = 50;
    f = fopen("/sys/class/thermal/thermal_zone2/temp", "r");
    if (!f) f = fopen("/sys/class/thermal/thermal_zone0/temp", "r");
    if (f) {
        int t = 0;
        if (fscanf(f, "%d", &t) == 1) temp = t / 1000;
        fclose(f);
    }

    // 5. CPU Frequency
    char ghz_str[32] = "3.4 GHz";
    f = fopen("/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq", "r");
    if (f) {
        long khz = 0;
        if (fscanf(f, "%ld", &khz) == 1 && khz > 0) {
            snprintf(ghz_str, sizeof(ghz_str), "%.1f GHz", (double)khz / 1000000.0);
        }
        fclose(f);
    }

    // Output: MEM_USED:::MEM_TOTAL:::MEM_PCT:::DISK_FREE:::DISK_PCT:::CPU_PCT:::TEMP:::CPU_GHZ
    printf("%.1f GB:::%.1f GB:::%d:::%.0fG:::%d:::%d:::%d:::%s\n",
           used_gb, total_gb, mem_pct, disk_free_gb, disk_pct, cpu_pct, temp, ghz_str);

    return 0;
}
