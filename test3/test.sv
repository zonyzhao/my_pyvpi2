module top;
reg clk;
reg [7:0] a,b;
wire [8:0] o;

always begin
    #10us
    clk = ~clk;
end

assign o = a+b;

initial begin
    $monitor("%0d: a=%b ; b=%b ; o=%b; c=%b",$time, a,b,o,clk);
end

initial begin
    a = 0;
    b = 0;
    clk = 1'b0;
    $pyvpi_main("1.py");
end

// initial begin
//     #10us
//     // repeat(5) begin
//     //     #10us;
//     //     a = a+1;
//     // end
// end

initial begin
//    $pyvpi_main("/workspaces/dzhao/python/test.py");
    #1us
    $finish(0);
end

endmodule
