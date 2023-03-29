in
sto char
// Output newline character x0A
ldm &0A
out
loop: ldd char
inc acc
sto char
out
ldd count
inc acc
sto count
cmp max
jpn loop
end

char: #0
count: #0
max: #5
