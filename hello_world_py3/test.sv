`timescale 1ns/1ps
module top;

    reg [7:0]    a;
    reg [7:0]    b;
    reg [7:0]    c;

    initial begin
        $monitor("sv %t, a:%0d + b:%0d = c:%0d", $stime, a, b, c);
        b = 1;
        #20;
        #80;
        $finish;
    end

    always begin
        # 10
        $pyvpi_main("hello.py");
    end


    always @(*) begin
    	c = a + b;
    end


endmodule
