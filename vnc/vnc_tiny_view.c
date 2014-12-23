/*
 * vnc_tiny_view.c -- a simple vnc viewer 
 * for non-X11 displays. Supporting
 * ascii-art output and 
 * http://www.acmesystems.it/ledpanel
 *
 * (C) 2014 Juergen Weigert <jw@owncloud.com>
 * Distribute under LGPL-2.0+ or ask.
 * 
 * Code taken from GTK VNC Widget.
 * Below is the copyright of github/gtk-vnc/src/vncconnection.c
 */
/*
 * GTK VNC Widget
 *
 * Copyright (C) 2006  Anthony Liguori <anthony@codemonkey.ws>
 * Copyright (C) 2009-2010 Daniel P. Berrange <dan@berrange.com>
 *
 * This library is free software; you can redistribute it and/or
 * modify it under the terms of the GNU Lesser General Public
 * License as published by the Free Software Foundation; either
 * version 2.0 of the License, or (at your option) any later version.
 *
 * This library is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * Lesser General Public License for more details.
 *
 * You should have received a copy of the GNU Lesser General Public
 * License along with this library; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301 USA
 */
#include <stdio.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netdb.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <zlib.h>	// BuildRequires: zlib-devel

void cursor_up(int n)
{
  if (n < 1) n = 1;
  fprintf(stderr, "\x1b[%dA", n);
}

void rgb_ttyramp(int r, int g, int b)
{
  // http://paulbourke.net/dataformats/asciiart/
  unsigned int v = (r+g+b)/3;
  //static char ascii_ramp[] = " .-:=+*#%@";
  static char ascii_ramp[] = "$@B%8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/|()1{}[]?-_+~<>i!lI;:,\"^'. ";
  unsigned int i = v * (sizeof(ascii_ramp)-2) / 255;
  i = sizeof(ascii_ramp)-2-i;
  fputc(ascii_ramp[i], stderr);
  fputc(ascii_ramp[i], stderr);
}

void rgb_tty8c(int r, int g, int b)
{
  int dim = 1;
  int ansi = 0;

  if (r < 100) r = 0;
  if (g < 100) g = 0;
  if (b < 100) b = 0;
  if ((r >= 200) || (g >= 200) || (b >= 200)) dim = 0;
  if (r && g && b) ansi = 37;	// white
  else if (r && g) ansi = 33;	// yellow
  else if (r && b) ansi = 35;	// magenta
  else if (g && b) ansi = 36;	// cyan
  else if (r)      ansi = 31;	// red
  else if (g)      ansi = 32;	// green
  else if (b)      ansi = 34;	// blue
  else             ansi = 30;	// black

  fprintf(stderr, "\x1b[%d;1;%dm%s\x1b[0m", ansi, ansi+10, dim?"  ":"@@");
}

void draw_ttyc8(int ww, int hh, unsigned char *img)
{
  int h, w;
  cursor_up(hh+1);
  for (h = 0; h < hh; h++)
    {
      for (w = 0; w < ww; w++)
        {
          unsigned int r = *img++;
          unsigned int g = *img++;
          unsigned int b = *img++;
	  rgb_tty8c(r,g,b);
        }
      fprintf(stderr, "\r\n");
    }
}

void draw_ttyramp(int ww, int hh, unsigned char *img)
{
  int h, w;
  cursor_up(hh+1);
  for (h = 0; h < hh; h++)
    {
      for (w = 0; w < ww; w++)
        {
          unsigned int r = *img++;
          unsigned int g = *img++;
          unsigned int b = *img++;
	  rgb_ttyramp(r,g,b);
        }
      fprintf(stderr, "\r\n");
    }
}


void read_rgb_file(int w, int h, char *fname, unsigned char *buf)
{
  int i;
  FILE *fp = fopen(fname, "r");
  for (i = 0; i < w*h*3; i++)
    *buf++ = fgetc(fp); 
  fclose(fp);
}

typedef struct VncPixelFormat
{
  int bits_per_pixel;
  int depth;
  int byte_order;
  int true_color_flag;
  int red_max;
  int green_max;
  int blue_max;
  int red_shift;
  int green_shift;
  int blue_shift;
} VncPixelFormat;

typedef struct VncConnectionPrivate
{
  int absPointer;
  int major;
  int minor;
  int auth_type;
  int sharedFlag;
  int width;
  int height;
  int has_error;
  VncPixelFormat fmt;
  char *name;

  z_stream *strm;
  z_stream streams[5];

} VncConnectionPrivate;

typedef struct VncConnection
{
  int fd; 
  VncConnectionPrivate *priv;
} VncConnection;


// From /usr/include/glib-2.0/glib/gmacros.h
#define FALSE (0)
#define TRUE  (!FALSE)
// From /usr/include/glib-2.0/glib/gtypes.h
#define G_BIG_ENDIAN	4321
#define G_LITTLE_ENDIAN	1234

// FROM man getaddrinfo
VncConnection *connect_vnc_server(char *hostname, char *str_port)
{
  struct addrinfo hints;
  struct addrinfo *result, *rp;
  int sfd, s, j;
  size_t len;
  ssize_t nread;

  if (!str_port) str_port = "5900";

  memset(&hints, 0, sizeof(struct addrinfo));
  hints.ai_family = AF_INET;    /* Allow IPv4 or IPv6 */
  hints.ai_socktype = SOCK_STREAM;
  hints.ai_flags = 0;
  hints.ai_protocol = 0;          /* Any protocol */

  s = getaddrinfo(hostname, str_port, &hints, &result);
  if (s != 0) 
    {
      fprintf(stderr, "getaddrinfo: %s\n", gai_strerror(s));
      exit(EXIT_FAILURE);
    }

  for (rp = result; rp != NULL; rp = rp->ai_next) 
    {
      sfd = socket(rp->ai_family, rp->ai_socktype, rp->ai_protocol);
      if (sfd == -1) continue;

      if (connect(sfd, rp->ai_addr, rp->ai_addrlen) != -1) break;                  /* Success */

      close(sfd);
    }

  if (rp == NULL) 
    {               /* No address succeeded */
      fprintf(stderr, "Could not bind\n");
      exit(EXIT_FAILURE);
    }

  freeaddrinfo(result);           /* No longer needed */

  static VncConnection conn;
  static VncConnectionPrivate priv;

  priv.sharedFlag = TRUE;
  priv.has_error = FALSE;
  conn.priv = &priv;
  conn.fd = sfd;
  return &conn;
}


int vnc_connection_flush(VncConnection *conn)
{
  // we don't buffer for now.
}

int vnc_connection_read(VncConnection *conn, char *buf, int len)
{
  return read(conn->fd, buf, len);
}

unsigned char vnc_connection_read_u8(VncConnection *conn)
{
  u_int8_t value = 0;
  int r = read(conn->fd, &value, sizeof(value));
  return value;
}

unsigned char vnc_connection_read_u16(VncConnection *conn)
{
  u_int16_t value = 0;
  int r = read(conn->fd, &value, sizeof(value));
  return ntohs(value);
}

unsigned char vnc_connection_read_u32(VncConnection *conn)
{
  u_int32_t value = 0;
  int r = read(conn->fd, &value, sizeof(value));
  return ntohl(value);
}


int vnc_connection_write(VncConnection *conn, char *buf, int len)
{
  return write(conn->fd, buf, len);
}

int vnc_connection_write_u8(VncConnection *conn, u_int8_t value)
{
  return write(conn->fd, &value, sizeof(value));
}

int vnc_connection_write_u16(VncConnection *conn, u_int16_t value)
{
  value = htons(value);
  return write(conn->fd, &value, sizeof(value));
}

int vnc_connection_write_u32(VncConnection *conn, u_int32_t value)
{
  value = htonl(value);
  return write(conn->fd, &value, sizeof(value));
}


// FROM gtk-vnc/src/vncconnection.c

#define VNC_CONNECTION_AUTH_NONE 1

static int vnc_connection_before_version (VncConnection *conn, int major, int minor)
{
  VncConnectionPrivate *priv = conn->priv;

  return (priv->major < major) || (priv->major == major && priv->minor < minor);
}

static int vnc_connection_after_version (VncConnection *conn, int major, int minor)
{
  return !vnc_connection_before_version (conn, major, minor+1);
}

int vnc_connection_has_error(VncConnection *conn)
{
    VncConnectionPrivate *priv = conn->priv;

    return priv->has_error;
}

static void vnc_connection_read_pixel_format(VncConnection *conn, VncPixelFormat *fmt)
{
    unsigned char pad[3];

    fmt->bits_per_pixel  = vnc_connection_read_u8(conn);
    fmt->depth           = vnc_connection_read_u8(conn);
    fmt->byte_order      = vnc_connection_read_u8(conn) ? G_BIG_ENDIAN : G_LITTLE_ENDIAN;
    fmt->true_color_flag = vnc_connection_read_u8(conn);

    fmt->red_max         = vnc_connection_read_u16(conn);
    fmt->green_max       = vnc_connection_read_u16(conn);
    fmt->blue_max        = vnc_connection_read_u16(conn);

    fmt->red_shift       = vnc_connection_read_u8(conn);
    fmt->green_shift     = vnc_connection_read_u8(conn);
    fmt->blue_shift      = vnc_connection_read_u8(conn);

    vnc_connection_read(conn, pad, 3);

    fprintf(stderr, "Pixel format BPP: %d,  Depth: %d, Byte order: %d, True color: %d\n"
              "             Mask  red: %3d, green: %3d, blue: %3d\n"
              "             Shift red: %3d, green: %3d, blue: %3d\n",
              fmt->bits_per_pixel, fmt->depth, fmt->byte_order, fmt->true_color_flag,
              fmt->red_max, fmt->green_max, fmt->blue_max,
              fmt->red_shift, fmt->green_shift, fmt->blue_shift);
}


int vnc_connection_check_auth_result(VncConnection *conn)
{
  VncConnectionPrivate *priv = conn->priv;
  u_int32_t result = vnc_connection_read_u32(conn);
  if (!result) return TRUE;

  if (priv->minor >= 8) 
    {
      char reason[1024];
      int len = vnc_connection_read_u32(conn);

      if (len < 1 || len >= sizeof(reason)) { fprintf(stderr, "auth error: unkonw\n"); exit(4); }
      vnc_connection_read(conn, reason, len);
      reason[len] = '\0';
      fprintf(stderr, "auth error: Server says: %s\n", reason); 
      return FALSE;
    }
  return FALSE;
}

int vnc_connection_perform_auth(VncConnection *conn)
{
  VncConnectionPrivate *priv = conn->priv;
  unsigned int nauth, i;
  unsigned int auth[10];

  if (priv->minor <= 6) {
    nauth = 1;
    auth[0] = vnc_connection_read_u32(conn);
  } else {
    int auth_type_none_seen = 0;
    nauth = vnc_connection_read_u8(conn);
    if (nauth < 1 || nauth > 10) { fprintf(stderr, "nauth=%d out of range [1..10]\n", nauth); exit(2); }
    for (i = 0 ; i < nauth ; i++)
      {
        auth[i] = vnc_connection_read_u8(conn);
        if (auth[i] == VNC_CONNECTION_AUTH_NONE) auth_type_none_seen = 1;
      }
    if (!auth_type_none_seen) { fprintf(stderr, "Warn: only auth_type=1 (none) implemented. not offered by server.\n"); }
    priv->auth_type = VNC_CONNECTION_AUTH_NONE;
  }

  if (priv->minor > 6) {
    vnc_connection_write_u8(conn, priv->auth_type);
    vnc_connection_flush(conn);
  }

  if (priv->minor == 8)
    return vnc_connection_check_auth_result(conn);
}

int vnc_connection_initialize(VncConnection *conn)
{
  VncConnectionPrivate *priv = conn->priv;
  int ret, i;
  char version[13];
  char buf[BUFSIZ];

  vnc_connection_read(conn, version, 12);

  version[12] = 0;
  ret = sscanf(version, "RFB %03d.%03d\n", &priv->major, &priv->minor);
  if (ret != 2) {
        fprintf(stderr, "Error while parsing server version\n");
	exit(2);
  }

  fprintf(stderr, "Server version: %d.%d\n", priv->major, priv->minor);

  if (vnc_connection_before_version(conn, 3, 3)) {
        fprintf(stderr, "Server version is not supported (%d.%d)\n", priv->major, priv->minor);
        exit(3);
    } else if (vnc_connection_before_version(conn, 3, 7)) {
        priv->minor = 3;
    } else if (vnc_connection_after_version(conn, 3, 8)) {
        priv->major = 3;
        priv->minor = 8;
    }
  snprintf(version, 13, "RFB %03d.%03d\n", priv->major, priv->minor);
  vnc_connection_write(conn, version, 12);
  vnc_connection_flush(conn);

  fprintf(stderr, "Using version: %d.%d\n", priv->major, priv->minor);

  if (!vnc_connection_perform_auth(conn)) {
        fprintf(stderr,"Auth failed\n"); exit(4);
  }
  printf("authentication successful\n");
  vnc_connection_write_u8(conn, priv->sharedFlag);	// "\1"
  vnc_connection_flush(conn);

  priv->width = vnc_connection_read_u16(conn);	// "\0@"
  priv->height = vnc_connection_read_u16(conn);	// "\0@"

  if (vnc_connection_has_error(conn))
    return FALSE;
  fprintf(stderr, "Initial desktop size %dx%d\n", priv->width, priv->height);

  vnc_connection_read_pixel_format(conn, &priv->fmt);

  int n_name = vnc_connection_read_u32(conn);
  if (n_name > 4096)
    return FALSE;
  priv->name = (char *)calloc(sizeof(char), n_name + 1);

  vnc_connection_read(conn, priv->name, n_name);
  priv->name[n_name] = 0;
  fprintf(stderr, "Display name '%s'", priv->name);

  if (vnc_connection_has_error(conn))
    return FALSE;

  memset(&priv->streams, 0, sizeof(priv->streams));	// typo in gtk-vnc/src/vncconnection?
  /* FIXME what level? */
  for (i = 0; i < 5; i++)
    inflateInit(&priv->streams[i]);
  priv->strm = NULL;

  return TRUE;
}

int main(int ac, char **av)
{
#if 1
  VncConnection *conn = connect_vnc_server(av[1], av[2]);	// hostname [port]
  if (!vnc_connection_initialize(conn)) exit(8);
  
#else

  char buf[32*32*3];
  read_rgb_file(32, 32, av[1], buf);
  // draw_ttyc8(32,32,buf);
  draw_ttyramp(32,32,buf);
#endif
}
