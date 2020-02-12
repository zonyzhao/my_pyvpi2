module top;

    reg [31:0]    a;
    reg [31:0]    b;
    reg [31:0]    c;

    initial begin
        $monitor("sv %t, a:%0d + b:%0d = c:%0d", $time, a, b, c);
    end

    initial begin
        a = 0;
        b = 0;
        $pyvpi_main("hello.py");
        #10;
        a = 1;
        b = 2;
        #10;
        a = 2;
        b = 3;
    end

   initial begin
    #100;
    $finish;
   end

endmodule
