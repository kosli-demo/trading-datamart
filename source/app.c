#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <errno.h>
#include <sys/socket.h>
#include <netinet/in.h>

#define PORT 8000
#define DATETIME_FILE "/app/datetime.txt"

static int read_datetime(char *name, char *ts, char *err) {
    FILE *f = fopen(DATETIME_FILE, "r");
    if (!f) {
        sprintf(err, "cannot open datetime.txt: %s", strerror(errno));
        return -1;
    }
    int n = fscanf(f, "%127s %127s", name, ts);
    fclose(f);
    if (n < 2) {
        sprintf(err, "datetime.txt must contain two words");
        return -1;
    }
    return 0;
}

static void respond(int fd, int status, const char *body) {
    char hdr[256];
    const char *txt = status == 200 ? "OK" : status == 503 ? "Service Unavailable" : "Not Found";
    int len = strlen(body);
    snprintf(hdr, sizeof(hdr),
        "HTTP/1.1 %d %s\r\nContent-Type: application/json\r\nContent-Length: %d\r\nConnection: close\r\n\r\n",
        status, txt, len);
    write(fd, hdr, strlen(hdr));
    write(fd, body, len);
}

static void handle_alive(int fd) {
    respond(fd, 200, "{\"alive\":true}");
}

static void handle_ready(int fd) {
    char name[128], ts[128], err[256], body[512];
    if (read_datetime(name, ts, err) < 0) {
        snprintf(body, sizeof(body), "{\"ready\":false,\"reason\":\"%s\"}", err);
        respond(fd, 503, body);
    } else {
        respond(fd, 200, "{\"ready\":true}");
    }
}

static void handle_repo_name(int fd) {
    char name[128], ts[128], err[256], body[512];
    if (read_datetime(name, ts, err) < 0) { respond(fd, 503, "{\"detail\":\"cannot read datetime.txt\"}"); return; }
    snprintf(body, sizeof(body), "{\"repo-name\":\"%s\"}", name);
    respond(fd, 200, body);
}

static void handle_timestamp(int fd) {
    char name[128], ts[128], err[256], body[512];
    if (read_datetime(name, ts, err) < 0) { respond(fd, 503, "{\"detail\":\"cannot read datetime.txt\"}"); return; }
    snprintf(body, sizeof(body), "{\"timestamp\":\"%s\"}", ts);
    respond(fd, 200, body);
}

static void handle(int fd) {
    char buf[4096];
    int n = read(fd, buf, sizeof(buf) - 1);
    if (n <= 0) return;
    buf[n] = '\0';

    char method[8], path[256];
    if (sscanf(buf, "%7s %255s", method, path) != 2) return;
    if (strcmp(method, "GET") != 0) { respond(fd, 404, "{\"detail\":\"Not Found\"}"); return; }

    if      (strcmp(path, "/alive")     == 0) handle_alive(fd);
    else if (strcmp(path, "/ready")     == 0) handle_ready(fd);
    else if (strcmp(path, "/repo-name") == 0) handle_repo_name(fd);
    else if (strcmp(path, "/timestamp") == 0) handle_timestamp(fd);
    else respond(fd, 404, "{\"detail\":\"Not Found\"}");
}

int main(void) {
    int srv = socket(AF_INET, SOCK_STREAM, 0);
    int opt = 1;
    setsockopt(srv, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));
    struct sockaddr_in addr = { .sin_family = AF_INET, .sin_addr.s_addr = INADDR_ANY, .sin_port = htons(PORT) };
    bind(srv, (struct sockaddr *)&addr, sizeof(addr));
    listen(srv, 10);
    for (;;) {
        int fd = accept(srv, NULL, NULL);
        if (fd >= 0) { handle(fd); close(fd); }
    }
}
