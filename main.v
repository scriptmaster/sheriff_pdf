module main

import os
import math
import compress.zlib
import compress.deflate
import encoding.base64

fn main() {
    // println("hi from pdf_parser")

    pdf_file := "sample.pdf"
    
    pdf := os.read_lines(pdf_file) or {
        println("Cannot read bytes from pdf")
        return
    }

    mut i := 0
    mut prevline := ''
    mut decompressing := false

    for line in pdf[0..math.min(100,pdf.len)] {
        i += 1
        if (prevline != '' && prevline.ends_with('stream') && !prevline.ends_with('endstream')) || decompressing {
            ll := math.min(line.len, 200)
            //println('$i) preview:' + hex4(line[0..ll].bytes()) + '\n')
            if line == 'endstream' {
                decompressing = false
                //println('$i:' + hex4(line.bytes()) + '\n')
                println('$i:endstream:' + line.len.str() + '\n')
            } else {
                decompressing = true
                //println('zlib.decompress:')
                if line.len > 2 {
                    lb := line[0..].bytes() // 2.. does NOT work :/
                    // println("base64:${base64.encode(lb)}")
                    println('lb: ${lb[0..2]}')
                    dec_line := zlib.decompress(lb) or {''.bytes()}
                    //println('zlib:$i:' + hex4(dec_line) + '\n')
                    println('zlib:$i: ${dec_line} \n')
                    //println('$i:${line.len}:${dec_line.len}:${hex4(dec_line)}\n')
                    dfl := deflate.decompress(lb[2..]) or {''.bytes()}
                    // println('\ndeflate:${hex4(dfl)}')
                    println('\ndeflate:${dfl}')
                } else {
                    println('$i:${line.len}:' + hex4(line.bytes()) + '\n')
                }

                //println('zlib.deflate>')
                //dec_line2 := deflate.decompress(line[2..].bytes()) or {''.bytes()}
                //println('$i>' + hex4(dec_line2) + '\n')

            }
        } else {
            println('$i)' + hex4(line.bytes()) + '\n')
        }
        prevline = line
    }

    // println("size: ${pdf_file}")

    //mut i := 0
    //mut j := 0
    //width := 20
    //for {
    //    j = i + width
    //    println(hex4(pdf[i..j]))
    //    i = j
    //}
}

fn hex4(b []u8) string {
    mut sa := []string{ cap: b.len }
    for a in b {
        if a >= 32 && a <= 126 {
            sa << a.ascii_str()
        } else {
            sa << '—'
        }
    }

    //sa << '\n'
    sa << '\n' + b.len.str() + ']'

    mut sm := []string{ cap: b.len }
    mut i := 0
    mut j := 0
    for a in b {
        if a >= 32 && a <= 126 {
            sa << '·' + a.ascii_str()
            if j > 0 {
                sm << 'b' + j.str()
                j = 0
                i = 0
            }
            i += 1
        } else {
            sa << ' ' + a.hex()
            if i > 0 {
                sm << 'a' + i.str()
                i = 0
                j = 0
            }
            j += 1
        }
    }
    if j > 0 {
        sm << 'b' + j.str()
    } else {
        sm << 'a' + i.str()
    }

    sa << '\n==== ' + b.len.str() + ' = ' + sm.join(' + ')

    return sa.join('')
}

fn hex3(b []u8) string {
    mut sa := []string{ cap: b.len }
    for a in b {
        if a >= 32 && a <= 126 {
            sa << a.ascii_str()
        } else {
            sa << a.hex()
        }
    }
    return sa.join(' ')
}
