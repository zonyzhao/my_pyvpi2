
module top;

    reg [31:0]    a;
    reg [31:0]    b;
    reg [31:0]    c;
    
    wire [3:0]    wx;

    initial begin
        $monitor("sv %t, a:%0d + b:%0d = c:%0d", $time, a, b, c);
        #10 ;
        $pyvpi_main("3.py");
        $pyvpi_main("hello.py");

        #20
        b = 1;
        $monitor("sv 2 %t, a:%0d + b:%0d = c:%0d", $time, a, b, c);
        #10 ;
        $finish;
    end



endmodule
